from backend.app.rag.chunker import chunk_text
from backend.app.rag.embedder import embed_texts, embed_query
from backend.app.rag.vector_store import store_chunks, retrieve_similar
from typing import List, Dict, Any, Optional


def ingest_document(
    text: str,
    source: str = "unknown",
    collection_name: str = "nexusai_docs",
    user: str = "anonymous",
) -> Dict:
    """
    Full ingestion pipeline:
    raw text → chunks → embeddings → ChromaDB
    """
    chunks = chunk_text(text)
    if not chunks:
        return {"status": "error", "detail": "No chunks produced"}

    embeddings = embed_texts(chunks)
    metadata = [{"source": source, "user": user, "chunk_index": i}
                for i in range(len(chunks))]

    stored = store_chunks(chunks, embeddings, metadata, collection_name)
    return {
        "status": "success",
        "chunks_stored": stored,
        "source": source,
    }


def retrieve_context(
    query: str,
    top_k: int = 5,
    collection_name: str = "nexusai_docs",
    where: Optional[Dict] = None,
) -> str:
    """
    Retrieves relevant context for a query.
    Returns formatted string ready to inject into agent prompt.
    """
    query_emb = embed_query(query)
    results = retrieve_similar(query_emb, top_k, collection_name, where)

    if not results:
        return ""

    context_parts = []
    for i, r in enumerate(results):
        context_parts.append(
            f"[Source {i+1} | score={r['score']} | from={r['metadata'].get('source','?')}]\n{r['text']}"
        )
    return "\n\n".join(context_parts)