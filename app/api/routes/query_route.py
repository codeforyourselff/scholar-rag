from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_retrival_service
from app.api.schemas import SearchQuery
from app.domain.models import SearchResult
from app.modules.retrieval.service import DocumentRetrievalService

"""Search query router api endpoint"""
router = APIRouter(prefix="/query", tags=["Retrieval"])

@router.post("/")
async def search_documents(searchQuery:SearchQuery, service: DocumentRetrievalService = Depends(get_retrival_service))-> list[SearchResult]:
    try:
        results = await service.search(searchQuery)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))