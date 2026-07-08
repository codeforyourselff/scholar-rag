from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_retrival_service
from app.api.schemas import SearchQuery
from app.domain.models import EmbeddedChunk
from app.modules.retrieval.service import DocumentRetrievalService

"""Search query router api endpoint"""
router = APIRouter(prefix="/query", tags=["Retrieval"])

@router.post("/retrieve")
async def search_documents(request:SearchQuery, service: DocumentRetrievalService = Depends(get_retrival_service))-> list[EmbeddedChunk]:
    try:
        results = await service.execute(user_query=request.query, limit=request.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/ingestion")
async def ingest_documents():
    return {"message": "The route is under construction."}