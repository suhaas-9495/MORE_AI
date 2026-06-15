from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.rag.pipeline import ingest_document, retrieve_context
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=10)
    source: str = Field(default="manual", description="Document source label")
    collection: str = Field(default="nexusai_docs")


class IngestResponse(BaseModel):
    status: str
    chunks_stored: int
    source: str


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    collection: str = Field(default="nexusai_docs")


class RetrieveResponse(BaseModel):
    query: str
    context: str
    collection: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    payload: IngestRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = ingest_document(
            text=payload.text,
            source=payload.source,
            collection_name=payload.collection,
            user=current_user["username"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return IngestResponse(**result)


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(
    payload: RetrieveRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        context = retrieve_context(
            query=payload.query,
            top_k=payload.top_k,
            collection_name=payload.collection,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RetrieveResponse(
        query=payload.query,
        context=context,
        collection=payload.collection,
    )