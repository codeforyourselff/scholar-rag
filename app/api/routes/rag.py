import logging
from fastapi import APIRouter
from fastapi import Depends
from app.api.deps import get_rag_use_case
from app.api.schemas import UserQueryRequest
from app.modules.rag.service import RAGUseCase
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