import os
import tempfile
import shutil
from uvicorn.config import logger
from app.modules.ingestion.loaders import TextStreamingLoader
from app.modules.ingestion.service import DocumentIngestionService
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from app.api.deps import get_ingestion_service, get_retrieval_service
from app.api.schema import SearchQuery
from app.domain.models import DocumentMetaData, EmbeddedChunk
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
        raise HTTPException(status_code=500, detail=f"An error occurred while searching documents.")

@router.post("/ingestion", response_model=int)
async def ingest_documents(file:UploadFile = File(...),title:str = Form(default=None), author:str = Form(default=None), service:DocumentIngestionService = Depends(get_ingestion_service)):

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name not provided")

    meta_data= DocumentMetaData(
        source_id=file.filename,
        title=title,
        author=author
    )
    temp_path = ''
    try:
        fd, temp_path= tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd,"wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Instantiate the text streaming into router for future scopes
        text_streaming_loader:TextStreamingLoader = TextStreamingLoader(file_path=temp_path)

        # Instantiate the document ingestion service
        final_result = await service.execute(text_stream=text_streaming_loader.stream_text(),metadata=meta_data)
        return final_result

    except Exception as e:
        logger.error({'Message':'Error in ingest_documents', 'Detail': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occured while ingesting documents.")
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
