import logging
from app.modules.generation.service import RAGUseCase
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_rag_use_case
from app.api.schema import UserQueryRequest
from app.domain.models import RAGResponseModel

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/rag", tags=["Retrieval"])

@router.post("/ask",response_model=RAGResponseModel)
async def ask_question(request:UserQueryRequest,service: RAGUseCase = Depends(get_rag_use_case)):
    try:
        results = await service.execute(user_query=request.user_query)
        return results
    except Exception as e:
        logging.error({'Message':'Error in ask_question', 'Detail': str(e)})
        raise HTTPException(status_code=500, detail=f"An error occurred while asking question.")