import chromadb
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
import uuid

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return _client


def get_collection(collection_name: str = "nexusai_docs"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def store_chunks(
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[List[Dict]] = None,
    collection_name: str = "nexusai_docs",
) -> int:
    collection = get_collection(collection_name)
    ids = [str(uuid.uuid4()) for _ in chunks]
    meta = metadata or [{}] * len(chunks)

    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=meta)
    return len(chunks)


def retrieve_similar(
    query_embedding: List[float],
    top_k: int = 5,
    collection_name: str = "nexusai_docs",
    user: Optional[str] = None,
    source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieval with metadata filtering.
    user=  → only this user's documents (data isolation, security requirement)
    source= → only docs from a specific source/file
    """
    collection = get_collection(collection_name)

    # build ChromaDB where clause dynamically
    where_clause = {}
    if user and source:
        where_clause = {"$and": [{"user": user}, {"source": source}]}
    elif user:
        where_clause = {"user": user}
    elif source:
        where_clause = {"source": source}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause or None,
        include=["documents", "distances", "metadatas"],
    )

    if not results["documents"][0]:
        return []

    output = []
    for doc, dist, meta in zip(
        results["documents"][0], results["distances"][0], results["metadatas"][0]
    ):
        output.append({
            "text": doc,
            "score": round(1 - dist, 4),
            "metadata": meta,
        })
    return output


def delete_user_documents(user: str, collection_name: str = "nexusai_docs") -> int:
    """GDPR-style cleanup — delete all of a user's ingested docs."""
    collection = get_collection(collection_name)
    collection.delete(where={"user": user})
    return 1