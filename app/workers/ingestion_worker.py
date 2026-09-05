import asyncio
import logging
from app.core.celery import celery_app
from app.container import get_container
from app.config import Settings, get_settings
from celery.signals import worker_process_init, worker_process_shutdown

logger = logging.getLogger(__name__)
worker_container = None

@worker_process_init.connect
def init_worker_container(**kwargs):
    """
    Executes exactly once when a Celery worker process starts.
    """
    global worker_container
    settings: Settings = get_settings()
    worker_container = get_container(settings)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker_container.startup())
    logger.info("Worker container initialized.")
    print("Celery worker process initialized DI container.")

@worker_process_shutdown.connect
def shutdown_worker_container(**kwargs):
    """
    Executes exactly once when a Celery worker process is shutting down.
    """
    global worker_container
    if worker_container:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(worker_container.shutdown())
        logger.info("Worker container shutdown completed.")
        print("Celery worker process shutdown DI container.")

@celery_app.celery.task(bind=True, name="tasks.process_academic_file_task", acks_late=True, autoretry_for=(ConnectionError, TimeoutError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_academic_file_task(self, file_path: str, tenant_id: str):
   """Pure task execution.No container lifecycle management here,"""
   logger.info(f"Starting task for tenant_id: {tenant_id} with file_path: {file_path}")

   try:
       # Access the globally initialized worker container
        global worker_container

        # Ask the container for the synchronous Use case
        academic_ingestion_use_case = worker_container.get_academic_ingestion_service()
        return academic_ingestion_use_case.process_file(file_path=file_path, document_id=tenant_id)
   except Exception as e:
       logger.error(f"Error processing academic file for tenant_id: {tenant_id}. Error: {e}", exc_info=True)
       raise e