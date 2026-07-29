import os
import tempfile
import shutil
from celery import Celery
import magic
from celery.result import AsyncResult
from uvicorn.config import logger
from app.core.celery import celery_app
from app.modules.ingestion.loaders import TextStreamingLoader
from app.modules.ingestion.service import DocumentIngestionService
from app.api.deps import get_ingestion_service, get_retrieval_service
from app.api.schema import SearchQuery
from app.domain.models import DocumentMetaData, EmbeddedChunk
from app.modules.retrieval.service import DocumentRetrievalService
from app.workers.ingestion_worker import process_academic_file_task
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form


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

@router.post("/ingestion_academic", response_model=dict)
async def ingestion_academic(file:UploadFile = File(...)):
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
        task = process_academic_file_task.delay(temp_path,"123")
        return {
            "job_id": task.id,
            "status": "accepted",
            "message": "File spooled and queued for background ML processing."
        }

    except Exception as e:
        logger.error({'Message':'Error in ingest_documents', 'Detail': str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occured while ingesting documents.")

@router.post("/ingestion_status/{job_id}", response_model=dict)
async def get_ingestion_status(job_id: str):
    """Clean URL-encoded or escaped double quotes sent by the client"""
    clean_job_id = job_id.strip('"').strip("'").strip()

    if not clean_job_id:
        raise HTTPException(status_code=400, detail="Invalid job_id format.")
    
    """Fetch the task state from Redis"""
    celery: Celery = celery_app.celery
    task_result = AsyncResult(id=job_id,app=celery)

    """Check task_result states"""
    if not task_result.ready():
        return {
            "job_id": clean_job_id,
            "status": task_result.state,
            "result": None
        }
    
    if task_result.successful():
        return {
            "job_id": job_id, 
            "status": task_result.state, 
            "result": task_result.result
        }
    else:
        return {
            "job_id": job_id, 
            "status": task_result.state, 
            "error": str(task_result.info)
        }
    