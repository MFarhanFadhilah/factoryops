import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import RAG_DIR, RAG_MANIFEST_CSV

CHUNK_WORDS = 650
OVERLAP_WORDS = 100
INDEX_CACHE = RAG_DIR / "_index_cache.json"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _find_source(filename):
    matches = list(RAG_DIR.rglob(filename))
    return matches[0] if matches else None


def _extract_pages(path):
    """Returns a list of (page_number_or_None, text)."""
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
        except ImportError:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                return [(i + 1, page.extract_text() or "") for i, page in enumerate(pdf.pages)]
    return [(None, path.read_text(encoding="utf-8", errors="ignore"))]


def _chunk_words(words, size, overlap):
    if not words:
        return []
    step = max(size - overlap, 1)
    chunks = []
    for start in range(0, len(words), step):
        piece = words[start : start + size]
        if not piece:
            break
        chunks.append(" ".join(piece))
        if start + size >= len(words):
            break
    return chunks


def build_index():
    """Chunks every manifest document, verifies SHA-256 provenance, and caches the result."""
    entries = []
    integrity_issues = []

    with open(RAG_MANIFEST_CSV, newline="") as f:
        for row in csv.DictReader(f):
            filename = row["file"]
            path = _find_source(filename)
            if path is None:
                integrity_issues.append({"file": filename, "issue": "missing_on_disk"})
                continue

            actual_sha = _sha256(path)
            if actual_sha != row["sha256"]:
                integrity_issues.append(
                    {"file": filename, "issue": "sha256_mismatch", "expected": row["sha256"], "actual": actual_sha}
                )
                continue

            for page_no, text in _extract_pages(path):
                words = text.split()
                for idx, chunk_text in enumerate(_chunk_words(words, CHUNK_WORDS, OVERLAP_WORDS)):
                    entries.append(
                        {
                            "document": filename,
                            "classification": row["classification"],
                            "page": page_no,
                            "chunk": f"c{idx}",
                            "sha256": actual_sha,
                            "text": chunk_text,
                        }
                    )

    cache = {"entries": entries, "integrity_issues": integrity_issues}
    INDEX_CACHE.write_text(json.dumps(cache))
    return cache


def _load_index():
    if INDEX_CACHE.exists():
        try:
            return json.loads(INDEX_CACHE.read_text())
        except json.JSONDecodeError:
            pass
    return build_index()


def _tfidf_vectors(entries, query_tokens):
    docs_tokens = [_tokenize(e["text"]) for e in entries]
    df = Counter()
    for tokens in docs_tokens:
        for term in set(tokens):
            df[term] += 1
    n_docs = max(len(docs_tokens), 1)

    def idf(term):
        return math.log((n_docs + 1) / (df.get(term, 0) + 1)) + 1.0

    query_tf = Counter(query_tokens)
    scores = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        score = 0.0
        for term, q_count in query_tf.items():
            if term in tf:
                score += q_count * tf[term] * idf(term)
        norm = math.sqrt(sum((tf[t] * idf(t)) ** 2 for t in tf)) or 1.0
        scores.append(score / norm)
    return scores


def search_rag_documents(query, document_types=None, top_k=4):
    """Read-only. Lexical TF-IDF retrieval with an optional local rerank-by-score pass.

    document_types: optional list to filter by manifest classification, e.g.
    ["regulation/guidance/manual"] or ["synthetic non-production SOP"].
    """
    index = _load_index()
    entries = index["entries"]

    if document_types:
        wanted = [d.lower() for d in document_types]
        entries = [e for e in entries if any(w in e["classification"].lower() for w in wanted)]

    if not entries:
        return {
            "query": query,
            "results": [],
            "integrity_issues": index["integrity_issues"],
            "note": "no matching documents for the given document_types filter",
        }

    query_tokens = _tokenize(query)
    scores = _tfidf_vectors(entries, query_tokens)
    ranked = sorted(zip(scores, entries), key=lambda pair: pair[0], reverse=True)
    ranked = [pair for pair in ranked if pair[0] > 0][:top_k]

    results = [
        {
            "document": e["document"],
            "classification": e["classification"],
            "page": e["page"],
            "chunk": e["chunk"],
            "sha256": e["sha256"],
            "score": round(score, 4),
            "excerpt": e["text"][:600],
        }
        for score, e in ranked
    ]

    return {
        "query": query,
        "result_count": len(results),
        "results": results,
        "integrity_issues": index["integrity_issues"],
    }


if __name__ == "__main__":
    build_index()
    print(json.dumps(search_rag_documents("tablet weight variation sampling", top_k=3), indent=2)[:2000])
