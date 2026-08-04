import logging
from app.config import Settings, get_settings
from app.container import Container, get_container
from app.core.celery import celery_app

logger = logging.getLogger(__name__)

@celery_app.celery.task(bind=True, name="tasks.process_academic_file")
async def process_academic_file_task(self, file_path: str, tenant_id: str):
    logger.info(f"Starting isolated parsing for {file_path}")

    # instantiate the container
    settings:Settings = get_settings()
    container:Container = get_container(settings)
    academic_ingestion_use_case = container.get_academic_ingestion_service()
    # calling the use_case service to process the file
    return await academic_ingestion_use_case.process_file(file_path=file_path)
    