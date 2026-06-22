from backend.app.rag.chunker import chunk_text
from backend.app.rag.embedder import embed_texts, embed_query
from backend.app.rag.vector_store import store_chunks, retrieve_similar, get_collection
from backend.app.rag.hybrid_search import keyword_search, hybrid_merge
from typing import Dict, Optional


def ingest_document(
    text: str,
    source: str = "unknown",
    collection_name: str = "nexusai_docs",
    user: str = "anonymous",
) -> Dict:
    chunks = chunk_text(text)
    if not chunks:
        return {"status": "error", "detail": "No chunks produced"}

    embeddings = embed_texts(chunks)
    metadata = [
        {"source": source, "user": user, "chunk_index": i}
        for i in range(len(chunks))
    ]
    stored = store_chunks(chunks, embeddings, metadata, collection_name)
    return {"status": "success", "chunks_stored": stored, "source": source}


def retrieve_context(
    query: str,
    top_k: int = 5,
    collection_name: str = "nexusai_docs",
    user: Optional[str] = None,
    source: Optional[str] = None,
    use_hybrid: bool = True,
) -> str:
    """
    Retrieval pipeline with hybrid search + user scoping.
    user= ensures users only retrieve their own ingested documents —
    this is the RAG Security requirement (data isolation).
    """
    query_emb = embed_query(query)
    semantic_results = retrieve_similar(
        query_emb, top_k=top_k * 2, collection_name=collection_name,
        user=user, source=source,
    )

    if not semantic_results:
        return ""

    if use_hybrid:
        all_docs = [r["text"] for r in semantic_results]
        keyword_results = keyword_search(query, all_docs, top_k=top_k * 2)
        merged = hybrid_merge(semantic_results, keyword_results)[:top_k]
    else:
        merged = semantic_results[:top_k]

    context_parts = []
    for i, r in enumerate(merged):
        src = r.get("metadata", {}).get("source", "?")
        context_parts.append(f"[Source {i+1} | score={round(r['score'],3)} | from={src}]\n{r['text']}")

    return "\n\n".join(context_parts)