import os
import re
import json
import math
from typing import List, Dict, Any

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
            for token in query_tokens:
                if token in frequencies:
                    tf = frequencies[token]
                    idf = self.idf.get(token, 0.0)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * (numerator / denominator)

            # Extra weight if terms appear in the document title
            title_tokens = set(self._tokenize(doc.get("title", "")))
            matching_title_tokens = sum(1 for t in query_tokens if t in title_tokens)
            score += matching_title_tokens * 2.5

            if score > 0.01:
                scored_results.append({
                    "score": round(score, 3),
                    **doc
                })

        # 3. Sort strictly by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

def chunk_documents(docs_path: str = None, chunk_size: int = 800, chunk_overlap: int = 150) -> List[Dict[str, Any]]:
    if docs_path is None:
        docs_path = os.path.join(os.path.dirname(__file__), "data", "documents.json")

    if not os.path.exists(docs_path):
        return []

    with open(docs_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    chunks = []
    for doc in docs:
        text = doc.get("content", "")
        if not text:
            continue

        paragraphs = text.split("\n\n")
        current_chunk = ""

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            if len(current_chunk) + len(p) <= chunk_size:
                current_chunk += "\n" + p if current_chunk else p
            else:
                if current_chunk:
                    chunks.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "chapter": doc.get("chapter", ""),
                        "programs": doc["programs"],
                        "published_on": doc.get("published_on", ""),
                        "local_pdf_url": doc.get("local_pdf_url", f"/pdfs/{doc['id']}.pdf"),
                        "official_url": doc["official_url"],
                        "summary": doc.get("summary", ""),
                        "text": f"[{' / '.join(doc['programs'])} - {doc['title']}]\n{current_chunk}"
                    })
                # Overlap
                current_chunk = current_chunk[-chunk_overlap:] + "\n" + p if len(current_chunk) > chunk_overlap else p

        if current_chunk:
            chunks.append({
                "id": doc["id"],
                "title": doc["title"],
                "chapter": doc.get("chapter", ""),
                "programs": doc["programs"],
                "published_on": doc.get("published_on", ""),
                "local_pdf_url": doc.get("local_pdf_url", f"/pdfs/{doc['id']}.pdf"),
                "official_url": doc["official_url"],
                "summary": doc.get("summary", ""),
                "text": f"[{' / '.join(doc['programs'])} - {doc['title']}]\n{current_chunk}"
            })

    return chunks

if __name__ == "__main__":
    chunks = chunk_documents()
    print(f"Generated {len(chunks)} chunks.")
    if chunks:
        index = BM25Index()
        index.build(chunks)
        results = index.search("college student work hours", program_filter="CalFresh")
        print(f"Test search found {len(results)} matches.")
