"""Small offline benchmark for the policy search engines.

Run with:  python3 evaluate_search.py

Each case is (query, program, expected section numbers).  A hit means any
expected section appears in the top 5 results.  MRR uses the first hit.
"""

import time

from indexer import BM25Index, chunk_documents
from search_engine import get_engine

CASES = [
    ("household concept", "CalFresh", ["63-101"]),
    ("students", "CalFresh", ["63-162"]),
    ("student eligibility 20 hours", "CalFresh", ["63-162"]),
    ("SAR 7 processing", "CalFresh", ["63-274"]),
    ("semi annual report cycle", "CalFresh", ["63-272"]),
    ("expedited services", "CalFresh", ["63-105"]),
    ("standard utility allowance", "CalFresh", ["63-235"]),
    ("categorical eligibility", "CalFresh", ["63-120"]),
    ("able bodied adults without dependents", "CalFresh", ["63-904"]),
    ("abad", "CalFresh", ["63-904"]),
    ("income limits", "CalFresh", ["63-1101"]),
    ("welfare to work sequence", "CalWORKs", ["10-005"]),
    ("wtw 30 hours", "CalWORKs", ["10-005"]),
    ("immediate need", "CalWORKs", ["40-100"]),
    ("maximum aid payment", "CalWORKs", ["44-300", "45-200"]),
    ("property", "CalWORKs", ["42-200"]),
    ("postpartum benefits", "Medi-Cal", ["Section 06"]),
    ("asset elimination", "Medi-Cal", ["SN 23-06"]),
    ("trusts and annuities", "Medi-Cal", ["Section 14"]),
    ("residency requirements", "Medi-Cal", ["Section 08"]),
    ("63-101", "CalFresh", ["63-101"]),
    ("10-005", "CalWORKs", ["10-005"]),
    ("sua", "CalFresh", ["63-235"]),
    ("food stamps", "CalFresh", ["63-156", "63-101", "63-162"]),
    ("calfrsh", "CalFresh", ["63-608", "63-101", "63-162", "63-1101", "63-330", "63-321"]),
]


def section_key(value):
    return (value or "").strip().lower()


def score(results, expected):
    expected = {section_key(x) for x in expected}
    ranks = []
    for i, result in enumerate(results, start=1):
        if section_key(result.get("section_num", "")) in expected:
            ranks.append(i)
    if not ranks:
        return 0.0, 0.0
    return 1.0, 1.0 / ranks[0]


def run(label, search_fn):
    hits = 0
    reciprocal = 0.0
    total_ms = 0.0
    misses = []
    for query, program, expected in CASES:
        started = time.time()
        results = search_fn(query, program, 5)
        total_ms += (time.time() - started) * 1000
        hit, rr = score(results, expected)
        hits += hit
        reciprocal += rr
        if not hit:
            top = results[0] if results else None
            misses.append((query, top.get("section_num", "—") if top else "—"))
    n = len(CASES)
    print(f"\n{label}")
    print(f"  Recall@5: {hits}/{n} ({hits / n:.0%})")
    print(f"  MRR:      {reciprocal / n:.3f}")
    print(f"  Avg time: {total_ms / n:.1f} ms")
    if misses:
        print("  Misses:")
        for query, top in misses:
            print(f"    - {query!r} (top: {top})")


def main():
    print("Building baseline BM25 over the same chunks…")
    started = time.time()
    baseline = BM25Index()
    baseline.build(chunk_documents())
    print(f"  built in {time.time() - started:.2f}s")

    engine = get_engine()
    print(f"  new engine: {engine.stats()}")

    run("Baseline BM25", lambda q, p, k: baseline.search(q, program_filter=p, top_k=k))
    run("SQLite FTS5", lambda q, p, k: engine.search(q, program_filter=p, top_k=k))


if __name__ == "__main__":
    main()
