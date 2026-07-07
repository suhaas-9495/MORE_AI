from typing import List, Dict, Optional
from datetime import datetime
import chromadb
from backend.app.core.config import settings
from backend.app.rag.embedder import embed_texts, embed_query

_client = None


def get_memory_collection(user: str):
    """
    Each user gets their own memory collection in ChromaDB.
    Long-term memory = semantically searchable history of past agent interactions.
    When a new task comes in, we retrieve similar past tasks + outcomes.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_db_path)

    collection_name = f"memory_{user.replace('-', '_')}"
    return _client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def store_memory(
    user: str,
    task: str,
    output: str,
    agent_type: str,
    success: bool = True,
):
    """
    Stores a task + outcome as a long-term memory entry.
    Called after every successful agent run.
    """
    collection = get_memory_collection(user)
    memory_text = f"Task: {task}\nOutcome: {output[:500]}\nSuccess: {success}"
    embedding = embed_texts([memory_text])[0]

    import uuid
    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[embedding],
        documents=[memory_text],
        metadatas=[{
            "user": user,
            "agent_type": agent_type,
            "task": task[:200],
            "success": str(success),
            "timestamp": datetime.utcnow().isoformat(),
        }],
    )


def retrieve_memories(user: str, query: str, top_k: int = 3) -> str:
    """
    Retrieves past relevant experiences for the current task.
    This is how the agent learns from its own history —
    similar past tasks surface with their outcomes.
    """
    collection = get_memory_collection(user)

    try:
        query_emb = embed_query(query)
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"][0]:
            return ""

        memories = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = round(1 - dist, 3)
            if score > 0.5:   # only surface highly relevant memories
                memories.append(
                    f"[Past experience | score={score} | {meta.get('timestamp','?')[:10]}]\n{doc}"
                )

        return "\n\n".join(memories) if memories else ""

    except Exception:
        return ""


def get_user_memory_stats(user: str) -> Dict:
    """How many memories does this user have stored?"""
    try:
        collection = get_memory_collection(user)
        count = collection.count()
        return {"user": user, "total_memories": count}
    except Exception:
        return {"user": user, "total_memories": 0}