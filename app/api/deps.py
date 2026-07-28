from fastapi import Request
from app.modules.ingestion.academic_service import AcademicIngestionUseCase
from app.modules.ingestion.service import DocumentIngestionService
from app.modules.retrieval.service import DocumentRetrievalService
from app.modules.generation.service import RAGUseCase

def get_retrieval_service(request:Request)-> DocumentRetrievalService:
    container = request.app.state.container
    return container.get_qdrant_vector_adapter()

def get_ingestion_service(request:Request)-> DocumentIngestionService:
    container = request.app.state.container
    return container.get_document_ingestion_service()

def get_academic_ingestion_service(request:Request)-> AcademicIngestionUseCase:
    container = request.app.state.container
    return container.get_academic_ingestion_service()

def get_rag_use_case(request:Request)-> RAGUseCase:
    container = request.app.state.container
    return container.get_rag_use_case()