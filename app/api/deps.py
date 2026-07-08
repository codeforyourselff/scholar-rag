from fastapi import Request
from app.modules.ingestion.service import DocumentIngestionService
from app.modules.retrieval.service import DocumentRetrievalService

def get_retrival_service(request:Request)-> DocumentRetrievalService:
    container = request.app.state.container
    return container.get_qdrant_vector_adapter()

def get_ingestion_service(request:Request)-> DocumentIngestionService:
    container = request.app.state.container
    return container.get_document_ingestion_service()