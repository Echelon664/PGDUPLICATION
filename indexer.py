import os
import re
import json
import math
from typing import List, Dict, Any

import catalog

class BM25Index:
    """Lightweight, zero-external-dependency BM25 full-text indexer."""
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self.docs: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\w+", text) if len(w) > 1]

    def build(self, documents: List[Dict[str, Any]]):
        self.docs = documents
        self.corpus_size = len(documents)
        total_len = 0
        tokenized_corpus = []

        for doc in documents:
            tokens = self._tokenize(doc["text"])
            tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_len.append(doc_len)
            total_len += doc_len

            frequencies = {}
            for token in tokens:
                frequencies[token] = frequencies.get(token, 0) + 1
            for token in frequencies:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avgdl = total_len / self.corpus_size if self.corpus_size > 0 else 0

        # Compute IDF
        for word, freq in self.doc_freqs.items():
            self.idf[word] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, program_filter: str = "All", top_k: int = 250) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)

        # 1. Strictly isolate candidate documents by program first
        candidate_indices = []
        for i, doc in enumerate(self.docs):
            if program_filter == "All":
                candidate_indices.append(i)
            else:
                doc_programs = doc.get("programs", [])
                if isinstance(doc_programs, str):
                    doc_programs = [doc_programs]
                if program_filter in doc_programs:
                    candidate_indices.append(i)

        if not candidate_indices:
            return []

        # 2. If query is empty, return unique program documents in chapter order!
        if not query_tokens:
            seen_ids = set()
            unique_docs = []
            for i in candidate_indices:
                doc = self.docs[i]
                if doc["id"] not in seen_ids:
                    seen_ids.add(doc["id"])
                    unique_docs.append({**doc, "score": 1.0})
            return unique_docs[:top_k]

        # 3. Score only documents that belong strictly to the selected program
        scored_results = []
        for i in candidate_indices:
            doc = self.docs[i]
            doc_tokens = self._tokenize(doc["text"])
            doc_len = self.doc_len[i]
            frequencies = {}
            for token in doc_tokens:
                frequencies[token] = frequencies.get(token, 0) + 1

            score = 0.0
            matched_terms = []
            for token in query_tokens:
                if token in frequencies:
                    tf = frequencies[token]
                    idf = self.idf.get(token, 0.0)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * (numerator / denominator)
                    matched_terms.append(token)

            # Extra weight if terms appear in the document title
            title_tokens = set(self._tokenize(doc.get("title", "")))
            matching_title_tokens = sum(1 for t in query_tokens if t in title_tokens)
            score += matching_title_tokens * 3.5

            # Boost if terms appear in summary
            summary_tokens = set(self._tokenize(doc.get("summary", "")))
            matching_summary_tokens = sum(1 for t in query_tokens if t in summary_tokens)
            score += matching_summary_tokens * 1.5

            if score > 0.01:
                scored_results.append({
                    "score": round(score, 3),
                    "matched_terms": matched_terms,
                    **doc
                })

        # Deduplicate by document ID, selecting highest score and best excerpt
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        unique_docs = {}
        for r in scored_results:
            did = r["id"]
            if did not in unique_docs:
                # Extract excerpt around matched query terms
                raw_text = r["text"]
                # remove [Program - Title] prefix if present
                clean_text = re.sub(r"^\[.*?\]\s*", "", raw_text).strip()
                tokens_in_text = [t for t in query_tokens if t in clean_text.lower()]
                excerpt = ""
                if tokens_in_text:
                    pos = clean_text.lower().find(tokens_in_text[0])
                    start = max(0, pos - 90)
                    end = min(len(clean_text), pos + 180)
                    if start > 0:
                        sp = clean_text.find(" ", start)
                        if sp != -1 and sp < pos: start = sp + 1
                    if end < len(clean_text):
                        sp = clean_text.rfind(" ", pos, end + 30)
                        if sp != -1 and sp > pos: end = sp
                    excerpt = clean_text[start:end].strip()
                    if start > 0: excerpt = "..." + excerpt
                    if end < len(clean_text): excerpt = excerpt + "..."
                else:
                    excerpt = clean_text[:220] + ("..." if len(clean_text) > 220 else "")

                unique_docs[did] = {
                    "id": r["id"],
                    "title": r["title"],
                    "chapter": r.get("chapter", ""),
                    "programs": r.get("programs", []),
                    "published_on": r.get("published_on", ""),
                    "local_pdf_url": r.get("local_pdf_url", ""),
                    "official_url": r.get("official_url", ""),
                    "source_missing": bool(r.get("source_missing")),
                    "pdf_date": r.get("pdf_date", ""),
                    "pdf_date_label": r.get("pdf_date_label", ""),
                    "summary": r.get("summary", ""),
                    "section_num": r.get("section_num", ""),
                    "section_title": r.get("section_title", ""),
                    "category": r.get("category", ""),
                    "score": r["score"],
                    "matched_excerpt": excerpt,
                    "matched_terms": list(set(r.get("matched_terms", []))),
                    "text": raw_text
                }

        results = list(unique_docs.values())
        return results[:top_k]

def chunk_documents(docs_path: str = None, chunk_size: int = 700, chunk_overlap: int = 120) -> List[Dict[str, Any]]:
    if docs_path is None:
        docs_path = os.path.join(os.path.dirname(__file__), "data", "documents.json")

    if not os.path.exists(docs_path):
        return []

    docs = catalog.load_documents(docs_path)

    def make_chunk(doc: Dict[str, Any], body: str) -> Dict[str, Any]:
        sec_prefix = f"{doc.get('section_num', '')} " if doc.get('section_num') else ""
        return {
            "id": doc["id"],
            "title": doc["title"],
            "chapter": doc.get("chapter", ""),
            "programs": doc["programs"],
            "published_on": doc.get("published_on", ""),
            "local_pdf_url": doc.get("local_pdf_url", ""),
            "official_url": doc["official_url"],
            "summary": doc.get("summary", ""),
            "section_num": doc.get("section_num", ""),
            "section_title": doc.get("section_title", ""),
            "category": doc.get("category", ""),
            "source_missing": bool(doc.get("source_missing")),
            "pdf_date": doc.get("pdf_date", ""),
            "pdf_date_label": doc.get("pdf_date_label", ""),
            "text": f"[{' / '.join(doc['programs'])} - {sec_prefix}{doc['title']}]\n{body}",
        }

    chunks = []
    for doc in docs:
        text = doc.get("content", "")
        if not text:
            # No source text (e.g. the County document is not bundled). Keep one
            # body-less chunk so the entry is still findable by title and section.
            chunks.append(make_chunk(doc, ""))
            continue

        # Split by sentence boundaries, double newlines, or single newlines
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)
        current_chunk = ""

        for p in parts:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk) + len(p) + 1 <= chunk_size:
                current_chunk = (current_chunk + " " + p).strip() if current_chunk else p
            else:
                if current_chunk:
                    chunks.append(make_chunk(doc, current_chunk))
                # Overlap
                current_chunk = (current_chunk[-chunk_overlap:] + " " + p).strip() if len(current_chunk) > chunk_overlap else p

        if current_chunk:
            chunks.append(make_chunk(doc, current_chunk))

    return chunks

if __name__ == "__main__":
    chunks = chunk_documents()
    print(f"Generated {len(chunks)} chunks.")
    if chunks:
        index = BM25Index()
        index.build(chunks)
        results = index.search("college student work hours", program_filter="CalFresh")
        print(f"Test search found {len(results)} matches.")
