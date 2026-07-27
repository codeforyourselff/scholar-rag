from app.domain.models import RAGResponseModel
from app.domain.ports.llm import LLMPort
from app.modules.retrieval.service import DocumentRetrievalService

class RAGUseCase:
    def __init__(self, llm_port: LLMPort, service: DocumentRetrievalService)-> None:
        self.service = service,
        self.llm_port= llm_port

    async def execute(self,query:str)-> RAGResponseModel:
        """On the first step we pass the query to the retriveal service"""
        ...