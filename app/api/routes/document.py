import os
import tempfile
import shutil
import magic
from uvicorn.config import logger
from app.modules.ingestion.loaders import TextStreamingLoader
from app.modules.ingestion.service import DocumentIngestionService
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from app.api.deps import get_academic_ingestion_service, get_ingestion_service, get_retrieval_service
from app.api.schema import SearchQuery
from app.domain.models import DocumentMetaData, EmbeddedChunk
from app.modules.retrieval.service import DocumentRetrievalService
from app.modules.ingestion.academic_service import AcademicIngestionUseCase


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

@router.post("/ingestion_text", response_model=int)
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

@router.post("/ingestion_academic", response_model=int)
async def ingestion_academic(file:UploadFile = File(...), service: AcademicIngestionUseCase = Depends(get_academic_ingestion_service)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name not provided")

    header = file.file.read(2048)
    mime_type = magic.from_buffer(header,mime=True)

    #Checking the type of the file
    if mime_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File not supported")
    
    # reset the cursor to 0 starts from beginning
    file.file.seek(0)
    temp_path = None
    try:    
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        # Usecase for parsed_doc
        parsed_doc = await service.process_file(temp_path)
        return parsed_doc

    except Exception as e:
        logger.error({'Message':'Error in ingest_documents', 'Detail': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occured while ingesting documents.")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)