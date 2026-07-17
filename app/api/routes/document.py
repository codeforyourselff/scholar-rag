from fastapi import APIRouter, Depends, HTTPException
from uvicorn.config import logger
from app.api.deps import get_retrieval_service
from app.api.schema import SearchQuery
from app.domain.models import EmbeddedChunk
from app.modules.retrieval.service import DocumentRetrievalService

"""Search query router api endpoint"""
router = APIRouter(prefix="/query", tags=["Retrieval"])

@router.post("/retrieve", response_model=list[EmbeddedChunk])
async def search_documents(request:SearchQuery, service: DocumentRetrievalService = Depends(get_retrieval_service)):
    try:
        results = await service.execute(user_query=request.query, limit=request.limit)
        return results
    except Exception as e:
        logger.error({'Message':'Error in search_documents', 'Detail': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while searching documents.")

@router.post("/ingestion")
async def ingest_documents():
    return {"message": "The route is under construction."}