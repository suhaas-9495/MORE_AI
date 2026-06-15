import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
import uuid

# persistent ChromaDB client — survives restarts
_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
        )
    return _client


def get_collection(collection_name: str = "nexusai_docs"):
    """
    Gets or creates a ChromaDB collection.
    Collections = namespaces. One per project/user in production.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for semantic search
    )


def store_chunks(
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[List[Dict]] = None,
    collection_name: str = "nexusai_docs",
) -> int:
    """
    Stores text chunks + their embeddings in ChromaDB.
    Each chunk gets a unique ID and optional metadata (source, page, user).
    Returns number of chunks stored.
    """
    collection = get_collection(collection_name)

    ids = [str(uuid.uuid4()) for _ in chunks]
    meta = metadata or [{}] * len(chunks)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=meta,
    )
    return len(chunks)


def retrieve_similar(
    query_embedding: List[float],
    top_k: int = 5,
    collection_name: str = "nexusai_docs",
    where: Optional[Dict] = None,          # metadata filtering
) -> List[Dict[str, Any]]:
    """
    Finds top-k most similar chunks to the query embedding.
    where= allows metadata filtering e.g. {"source": "auth_docs"}
    Returns list of {text, score, metadata}.
    """
    collection = get_collection(collection_name)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "distances", "metadatas"],
    )

    output = []
    for doc, dist, meta in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        output.append({
            "text": doc,
            "score": round(1 - dist, 4),   # cosine distance → similarity score
            "metadata": meta,
        })
    return output