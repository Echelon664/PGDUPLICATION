"""SQLite FTS5 search engine for the SDCounty HHSA policy guides.

The index lives in data/search.db and is rebuilt automatically when
data/documents.json changes.  A small query layer handles section codes,
acronyms, legacy program names, and phrase queries on top of FTS5's BM25
ranking.
"""

import json
import os
import re
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from indexer import BM25Index, chunk_documents

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCS_PATH = os.path.join(BASE_DIR, "data", "documents.json")
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "search.db")

# FTS5 column weights: doc_id (unindexed), section_num, title, summary, body.
FTS_WEIGHTS = (0.0, 20.0, 10.0, 4.0, 1.0)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
    "could", "did", "do", "does", "for", "from", "had", "has", "have", "how",
    "i", "if", "in", "into", "is", "it", "its", "may", "me", "might", "must",
    "my", "of", "on", "or", "our", "should", "so", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those", "to",
    "was", "we", "were", "what", "when", "where", "which", "who", "why",
    "will", "with", "would", "you", "your",
}

# Multi-word aliases are applied before tokenization so the alias survives
# as one query group.
MULTI_ALIASES: List[Tuple[re.Pattern, List[str]]] = [
    (re.compile(r"\bfood\s+stamps?\b", re.I),
     ["calfresh", "snap", '"food stamp"', '"food assistance"']),
    (re.compile(r"\bwelfare[\s-]+to[\s-]+work\b", re.I),
     ["wtw", '("welfare" AND "work")']),
    (re.compile(r"\bmedi[\s-]*cal\b", re.I),
     ['"medi cal"', "medicaid"]),
    (re.compile(r"\bsemi[\s-]*annual[\s-]+report(?:ing)?\b", re.I),
     ['"semi annual report"', "sar"]),
]

TOKEN_ALIASES: Dict[str, List[str]] = {
    "wtw": ["wtw", '("welfare" AND "work")'],
    "abad": ["abad", '("able" AND "bodied" AND "adults")'],
    "sua": ["sua", '("standard" AND "utility" AND "allowance")'],
    "sar": ["sar", '("semi" AND "annual" AND "report")'],
    "irt": ["irt", '("income" AND "reporting" AND "threshold")'],
    "snap": ["snap", "calfresh", '"food stamp"'],
    "calfresh": ["calfresh", "snap", '"food stamp"', '"food assistance"'],
    "calfrsh": ["calfresh"],
    "medicaid": ["medicaid", '"medi cal"'],
    "foodstamp": ["calfresh", "snap", '"food stamp"'],
    "foodstamps": ["calfresh", "snap", '"food stamp"'],
    "college": ["college", '"higher education"'],
    "university": ["university", "college", '"higher education"'],
}

CODE_RE = re.compile(
    r"\b(?:SN\s?\d{2}-\d{2}|Section\s+\d{1,3}|\d{2,3}-\d{2,4})\b",
    re.I,
)


def _fts5_available() -> bool:
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE _fts_probe USING fts5(x)")
        con.close()
        return True
    except Exception:
        return False


FTS5_AVAILABLE = _fts5_available()


def _quote(term: str) -> str:
    """Quote one token or phrase for FTS5 MATCH."""
    return '"' + term.replace('"', '') + '"'


def _program_clause(program: str, alias: str = "m") -> str:
    if program == "CalFresh":
        return f"AND {alias}.cf = 1"
    if program == "CalWORKs":
        return f"AND {alias}.cw = 1"
    if program == "Medi-Cal":
        return f"AND {alias}.mc = 1"
    return ""


def parse_query(query: str) -> Tuple[List[str], List[List[str]]]:
    """Return (section_codes, term_groups).

    Each term group is a list of alternative FTS5 expressions that should be
    OR'd together.  Groups are AND'd with each other.
    """
    q = (query or "").strip()
    codes = [m.group(0) for m in CODE_RE.finditer(q)]
    if codes:
        q = CODE_RE.sub(" ", q)

    alias_tokens: Dict[str, List[str]] = {}
    for i, (pattern, alternatives) in enumerate(MULTI_ALIASES):
        if pattern.search(q):
            token = f"zxalias{i}xz"
            q = pattern.sub(f" {token} ", q)
            alias_tokens[token] = alternatives

    # Quoted phrases are always treated as phrases.
    phrases = re.findall(r'"([^"]+)"', q)
    q = re.sub(r'"[^"]*"', " ", q)

    tokens = re.findall(r"[A-Za-z0-9]+", q.lower())
    filtered = [t for t in tokens if t not in STOPWORDS]
    if not filtered and tokens:
        filtered = tokens
    tokens = list(dict.fromkeys(filtered))

    groups: List[List[str]] = []
    for token in tokens:
        if token in alias_tokens:
            groups.append(alias_tokens[token])
        elif token in TOKEN_ALIASES:
            groups.append(TOKEN_ALIASES[token])
        else:
            groups.append([_quote(token)])

    for phrase in phrases:
        words = re.findall(r"[A-Za-z0-9]+", phrase.lower())
        words = [w for w in words if w not in STOPWORDS] or words
        if words:
            groups.append([_quote(" ".join(words))])

    return codes, groups


class SearchEngine:
    def __init__(self, docs_path: str = DEFAULT_DOCS_PATH, db_path: str = DEFAULT_DB_PATH):
        self.docs_path = docs_path
        self.db_path = db_path
        self._lock = threading.Lock()
        self._announced = False
        self._bm25: Optional[BM25Index] = None
        self._bm25_mtime = 0.0

        if FTS5_AVAILABLE:
            os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
            self.ensure_index()
        else:
            self._build_bm25()

    # ------------------------------------------------------------------ index
    def _build_bm25(self):
        self._bm25 = BM25Index()
        self._bm25.build(chunk_documents(self.docs_path))
        self._bm25_mtime = os.path.getmtime(self.docs_path)
        print(f"[search] FTS5 unavailable; using BM25 fallback ({len(self._bm25.docs)} chunks)")

    def _needs_rebuild(self) -> bool:
        if not os.path.exists(self.db_path):
            return True
        try:
            con = sqlite3.connect(self.db_path)
            row = con.execute(
                "SELECT value FROM index_meta WHERE key = 'docs_mtime'"
            ).fetchone()
            con.close()
            if not row:
                return True
            return abs(float(row[0]) - os.path.getmtime(self.docs_path)) > 1e-6
        except Exception:
            return True

    def ensure_index(self, force: bool = False):
        if not FTS5_AVAILABLE:
            if force or not self._bm25 or abs(os.path.getmtime(self.docs_path) - self._bm25_mtime) > 1e-6:
                self._build_bm25()
            return
        if not force and not self._needs_rebuild():
            self._announce()
            return
        with self._lock:
            if not force and not self._needs_rebuild():
                self._announce()
                return
            self._build()

    def _build(self):
        started = time.time()
        with open(self.docs_path, "r", encoding="utf-8") as f:
            docs = json.load(f)

        chunks = chunk_documents(self.docs_path)
        tmp_path = f"{self.db_path}.tmp.{os.getpid()}"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        con = sqlite3.connect(tmp_path)
        try:
            con.executescript(
                """
                PRAGMA journal_mode=OFF;
                PRAGMA synchronous=OFF;

                CREATE TABLE docs (
                    id TEXT PRIMARY KEY,
                    doc_order INTEGER,
                    title TEXT,
                    chapter TEXT,
                    programs TEXT,
                    published_on TEXT,
                    local_pdf_url TEXT,
                    official_url TEXT,
                    summary TEXT,
                    section_num TEXT,
                    section_title TEXT,
                    category TEXT,
                    category_desc TEXT,
                    category_id TEXT,
                    cf INTEGER,
                    cw INTEGER,
                    mc INTEGER,
                    content TEXT
                );

                CREATE VIRTUAL TABLE chunks USING fts5(
                    doc_id UNINDEXED,
                    section_num,
                    title,
                    summary,
                    body,
                    tokenize='porter unicode61'
                );

                CREATE TABLE index_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )

            doc_rows = []
            for order, doc in enumerate(docs):
                programs = doc.get("programs", [])
                doc_rows.append((
                    doc.get("id"),
                    order,
                    doc.get("title", ""),
                    doc.get("chapter", ""),
                    json.dumps(programs),
                    doc.get("published_on", ""),
                    doc.get("local_pdf_url", ""),
                    doc.get("official_url", ""),
                    doc.get("summary", ""),
                    doc.get("section_num", ""),
                    doc.get("section_title", ""),
                    doc.get("category", ""),
                    doc.get("category_desc", ""),
                    doc.get("category_id", ""),
                    1 if "CalFresh" in programs else 0,
                    1 if "CalWORKs" in programs else 0,
                    1 if "Medi-Cal" in programs else 0,
                    doc.get("content", ""),
                ))
            con.executemany(
                "INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                doc_rows,
            )

            chunk_rows = []
            for chunk in chunks:
                body = re.sub(r"^\[.*?\]\s*", "", chunk.get("text", ""))
                chunk_rows.append((
                    chunk.get("id"),
                    chunk.get("section_num", ""),
                    chunk.get("title", ""),
                    chunk.get("summary", ""),
                    body,
                ))
            con.executemany(
                "INSERT INTO chunks(doc_id, section_num, title, summary, body) VALUES (?,?,?,?,?)",
                chunk_rows,
            )

            con.executemany(
                "INSERT INTO index_meta(key, value) VALUES (?, ?)",
                [
                    ("docs_mtime", str(os.path.getmtime(self.docs_path))),
                    ("chunk_count", str(len(chunks))),
                    ("doc_count", str(len(docs))),
                    ("built_at", time.strftime("%Y-%m-%dT%H:%M:%S")),
                ],
            )
            con.commit()
        finally:
            con.close()

        os.replace(tmp_path, self.db_path)
        elapsed = time.time() - started
        print(
            f"[search] Built FTS5 index: {len(chunks)} chunks, "
            f"{len(docs)} documents in {elapsed:.2f}s"
        )
        self._announced = True

    def _announce(self):
        if self._announced:
            return
        try:
            con = sqlite3.connect(self.db_path)
            row = con.execute(
                "SELECT value FROM index_meta WHERE key = 'chunk_count'"
            ).fetchone()
            doc_row = con.execute(
                "SELECT value FROM index_meta WHERE key = 'doc_count'"
            ).fetchone()
            con.close()
            if row and doc_row:
                print(
                    f"[search] FTS5 index ready: {row[0]} chunks, {doc_row[0]} documents"
                )
        except Exception:
            pass
        self._announced = True

    # ----------------------------------------------------------------- search
    def search(
        self,
        query: str,
        program_filter: str = "All",
        top_k: int = 250,
    ) -> List[Dict[str, Any]]:
        if not FTS5_AVAILABLE:
            self.ensure_index()
            return self._bm25.search(query, program_filter=program_filter, top_k=top_k)  # type: ignore[union-attr]

        self.ensure_index()
        query = (query or "").strip()
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            if not query:
                return self._list_documents(con, program_filter, top_k)

            codes, groups = parse_query(query)
            exact_rows = self._fetch_codes(con, codes, program_filter, top_k)
            fts_rows: List[sqlite3.Row] = []

            if groups:
                candidate_limit = min(max(top_k * 6, 60), 500)
                and_expr = " AND ".join("(" + " OR ".join(g) + ")" for g in groups)
                fts_rows = self._fts_search(con, and_expr, program_filter, candidate_limit)
                if not fts_rows and len(groups) > 1:
                    or_expr = " OR ".join("(" + " OR ".join(g) + ")" for g in groups)
                    fts_rows = self._fts_search(con, or_expr, program_filter, candidate_limit)

            ranked = self._rerank(fts_rows, query)
            merged: List[Tuple[float, sqlite3.Row]] = [(100.0, row) for row in exact_rows]
            merged.extend(ranked)

            seen = set()
            results: List[Dict[str, Any]] = []
            for score_value, row in merged:
                doc_id = row["id"]
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                results.append(self._row_to_result(row, score_override=score_value))
                if len(results) >= top_k:
                    break
            return results
        finally:
            con.close()

    def _list_documents(self, con, program: str, limit: int) -> List[Dict[str, Any]]:
        where = _program_clause(program, "docs")
        if where:
            where = "WHERE " + where[4:]
        sql = (
            "SELECT docs.*, 0.0 AS fts_rank, '' AS excerpt, '' AS text "
            f"FROM docs {where} ORDER BY doc_order LIMIT ?"
        )
        rows = con.execute(sql, (limit,)).fetchall()
        return [self._row_to_result(row, no_query=True) for row in rows]

    def _fetch_codes(self, con, codes: List[str], program: str, limit: int) -> List[sqlite3.Row]:
        if not codes:
            return []
        clauses: List[str] = []
        params: List[Any] = []
        for code in dict.fromkeys(codes):
            code = code.strip()
            numeric = re.fullmatch(r"(\d{2,3})-(\d{2,4})", code)
            if numeric and len(numeric.group(2)) <= 2:
                clauses.append("LOWER(section_num) LIKE LOWER(?)")
                params.append(code + "%")
            else:
                clauses.append("LOWER(section_num) = LOWER(?)")
                params.append(code)
        where = " OR ".join(clauses)
        prog = _program_clause(program, "docs")
        sql = (
            "SELECT docs.*, 0.0 AS fts_rank, '' AS excerpt, docs.content AS text "
            f"FROM docs WHERE ({where}) {prog} ORDER BY doc_order LIMIT ?"
        )
        params.append(limit)
        return con.execute(sql, params).fetchall()

    def _rerank(self, rows: List[sqlite3.Row], query: str) -> List[Tuple[float, sqlite3.Row]]:
        """Boost documents whose titles contain the query or all query terms."""
        q_tokens = [
            t for t in re.findall(r"[A-Za-z0-9]+", query.lower())
            if t not in STOPWORDS
        ]
        if not q_tokens:
            return [(-float(row["fts_rank"] or 0.0), row) for row in rows]

        phrase = " ".join(q_tokens)
        ranked: List[Tuple[float, sqlite3.Row]] = []
        for row in rows:
            title = (row["title"] or "").lower().replace("-", " ")
            bonus = 15.0 if phrase and phrase in title else 0.0
            ranked.append((-float(row["fts_rank"] or 0.0) + bonus, row))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked

    def _fts_search(self, con, match: str, program: str, limit: int) -> List[sqlite3.Row]:
        prog = _program_clause(program, "m")
        sql = f"""
            WITH scored AS (
                SELECT m.*,
                       bm25(chunks, ?, ?, ?, ?, ?) AS fts_rank,
                       snippet(chunks, 4, '', '', '…', 32) AS excerpt,
                       chunks.body AS text
                FROM chunks
                JOIN docs m ON m.id = chunks.doc_id
                WHERE chunks MATCH ? {prog}
            ), ranked AS (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY fts_rank ASC) AS rn
                FROM scored
            )
            SELECT * FROM ranked WHERE rn = 1 ORDER BY fts_rank ASC LIMIT ?
        """
        params = list(FTS_WEIGHTS) + [match, limit]
        try:
            return con.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # A malformed MATCH expression should not take the API down.
            safe = " OR ".join(_quote(t) for t in re.findall(r"[A-Za-z0-9]+", match) if t)
            if not safe:
                return []
            return con.execute(sql, list(FTS_WEIGHTS) + [safe, limit]).fetchall()

    def _row_to_result(self, row: sqlite3.Row, no_query: bool = False,
                       score_override: Optional[float] = None) -> Dict[str, Any]:
        try:
            programs = json.loads(row["programs"]) if row["programs"] else []
        except (TypeError, ValueError):
            programs = []
        rank = row["fts_rank"] if "fts_rank" in row.keys() else 0.0
        if score_override is not None:
            score = round(float(score_override), 3)
        elif no_query:
            score = 1.0
        else:
            score = round(-float(rank or 0.0), 3)
        text = ""
        if not no_query:
            text = row["text"] or row["content"] or ""
        return {
            "id": row["id"],
            "title": row["title"],
            "chapter": row["chapter"],
            "programs": programs,
            "published_on": row["published_on"],
            "local_pdf_url": row["local_pdf_url"],
            "official_url": row["official_url"],
            "summary": row["summary"],
            "section_num": row["section_num"],
            "section_title": row["section_title"],
            "category": row["category"],
            "category_desc": row["category_desc"],
            "category_id": row["category_id"],
            "score": score,
            "matched_excerpt": row["excerpt"] or "",
            "matched_terms": [],
            "text": text,
        }

    def stats(self) -> Dict[str, Any]:
        if not FTS5_AVAILABLE:
            return {
                "engine": "bm25",
                "chunks": len(self._bm25.docs) if self._bm25 else 0,
            }
        try:
            con = sqlite3.connect(self.db_path)
            vals = dict(con.execute("SELECT key, value FROM index_meta").fetchall())
            con.close()
            return {
                "engine": "fts5",
                "docs": int(vals.get("doc_count", 0)),
                "chunks": int(vals.get("chunk_count", 0)),
                "built_at": vals.get("built_at", ""),
            }
        except Exception:
            return {"engine": "fts5", "docs": 0, "chunks": 0}


_ENGINE: Optional[SearchEngine] = None
_ENGINE_LOCK = threading.Lock()


def get_engine(docs_path: str = DEFAULT_DOCS_PATH, db_path: str = DEFAULT_DB_PATH) -> SearchEngine:
    global _ENGINE
    if _ENGINE is None:
        with _ENGINE_LOCK:
            if _ENGINE is None:
                _ENGINE = SearchEngine(docs_path=docs_path, db_path=db_path)
    return _ENGINE


if __name__ == "__main__":
    engine = get_engine()
    engine.ensure_index(force=True)
    print(engine.stats())
    for q, prog in [
        ("WTW 30 hours", "CalWORKs"),
        ("abad", "CalFresh"),
        ("food stamps", "CalFresh"),
        ("calfrsh", "CalFresh"),
        ("63-101", "CalFresh"),
        ("SAR 7", "CalFresh"),
        ("postpartum", "Medi-Cal"),
    ]:
        started = time.time()
        results = engine.search(q, prog, top_k=5)
        elapsed = (time.time() - started) * 1000
        print(f"\n{q!r} [{prog}] -> {len(results)} results in {elapsed:.1f} ms")
        for r in results[:3]:
            print(f"   {r['score']:7.2f}  {r['section_num']:10} {r['title'][:65]}")
