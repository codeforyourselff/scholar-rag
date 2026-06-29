from fastapi import Request
from app.modules.retrieval.service import DocumentRetrievalService

def get_retrival_service(request:Request)-> DocumentRetrievalService:
    container = request.app.state.container
    return container.get_qdrant_vector_adapter()