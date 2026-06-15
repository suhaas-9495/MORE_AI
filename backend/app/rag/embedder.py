from sentence_transformers import SentenceTransformer
from typing import List
from backend.app.core.config import settings

# loaded once at module level — expensive to reload every request
_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Converts text chunks into dense vectors.
    all-MiniLM-L6-v2: fast, 384-dim, good for semantic search.
    Returns list of float vectors — one per chunk.
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """Single query embedding for retrieval."""
    model = get_embedding_model()
    return model.encode([query])[0].tolist()