from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from backend.app.rag.pipeline import ingest_document, retrieve_context
from backend.app.rag.vector_store import delete_user_documents
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=10)
    source: str = Field(default="manual")
    collection: str = Field(default="nexusai_docs")


class IngestResponse(BaseModel):
    status: str
    chunks_stored: int
    source: str


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    collection: str = Field(default="nexusai_docs")
    own_documents_only: bool = Field(default=True, description="Security: scope to caller's own docs")


class RetrieveResponse(BaseModel):
    query: str
    context: str
    collection: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest(payload: IngestRequest, current_user: dict = Depends(get_current_user)):
    try:
        result = ingest_document(
            text=payload.text, source=payload.source,
            collection_name=payload.collection, user=current_user["username"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return IngestResponse(**result)


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(payload: RetrieveRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_filter = current_user["username"] if payload.own_documents_only else None
        context = retrieve_context(
            query=payload.query, top_k=payload.top_k,
            collection_name=payload.collection, user=user_filter,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RetrieveResponse(query=payload.query, context=context, collection=payload.collection)


@router.delete("/my-documents")
async def delete_my_documents(current_user: dict = Depends(get_current_user)):
    """GDPR-style self-service deletion."""
    delete_user_documents(user=current_user["username"])
    return {"status": "deleted", "user": current_user["username"]}