import asyncio
import logging
from app.config import Settings, get_settings
from app.container import Container, get_container
from app.core.celery import celery_app

logger = logging.getLogger(__name__)

@celery_app.celery.task(bind=True, name="tasks.process_academic_file_task", acks_late=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_academic_file_task(self, file_path: str, tenant_id: str):
    """
    Celery task that acts as the entry point for background processing.
    """
    logger.info(f"Starting isolated parsing for {file_path}")

    async def _run() -> dict:
        settings: Settings = get_settings()
        container: Container = get_container(settings)
        await container.startup()
        try:
            academic_ingestion_use_case = container.get_academic_ingestion_service()
            return await academic_ingestion_use_case.process_file(file_path=file_path,tenant_id=tenant_id)
        finally:
            await container.shutdown()

    return asyncio.run(_run())