from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import re


def tokenize(text: str) -> List[str]:
    """Simple tokenizer for BM25 — lowercase, split on non-alpha."""
    return re.findall(r"\w+", text.lower())


def keyword_search(query: str, documents: List[str], top_k: int = 5) -> List[Dict]:
    """
    BM25 keyword search — catches exact terms (error codes, function
    names, IDs) that semantic embeddings often miss.
    """
    if not documents:
        return []

    tokenized_docs = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(tokenize(query))

    ranked = sorted(
        zip(documents, scores), key=lambda x: x[1], reverse=True
    )[:top_k]

    return [{"text": doc, "bm25_score": round(score, 4)} for doc, score in ranked if score > 0]


def hybrid_merge(
    semantic_results: List[Dict],
    keyword_results: List[Dict],
    semantic_weight: float = 0.7,
) -> List[Dict]:
    """
    Combines semantic (embedding) + keyword (BM25) results.
    Weighted score: 70% semantic relevance, 30% exact keyword match.
    This is what production RAG systems use — pure semantic search
    misses exact terms; pure keyword misses paraphrased meaning.
    """
    combined: Dict[str, Dict] = {}

    for r in semantic_results:
        combined[r["text"]] = {
            "text": r["text"],
            "score": r["score"] * semantic_weight,
            "metadata": r.get("metadata", {}),
        }

    keyword_weight = 1 - semantic_weight
    max_bm25 = max([r["bm25_score"] for r in keyword_results], default=1) or 1

    for r in keyword_results:
        normalized = r["bm25_score"] / max_bm25
        if r["text"] in combined:
            combined[r["text"]]["score"] += normalized * keyword_weight
        else:
            combined[r["text"]] = {
                "text": r["text"],
                "score": normalized * keyword_weight,
                "metadata": {},
            }

    return sorted(combined.values(), key=lambda x: x["score"], reverse=True)