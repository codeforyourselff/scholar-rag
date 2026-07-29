import os
import asyncio
import logging
from app.config import Settings, get_settings
from app.container import get_container
from app.core.celery import celery_app

logger = logging.getLogger(__name__)

@celery_app.celery.task(bind=True, name="tasks.process_academic_file")
def process_academic_file_task(self, file_path: str, tenant_id: str):
    """Celery background task to process heavy academic PDFs."""

    async def _run():
        settings: Settings = get_settings()
        container = get_container(settings)
        await container.startup()
        service = container.get_academic_ingestion_service()
        return await service.process_file(file_path=file_path)
    try:
        asyncio.run(_run())
    except Exception as e:
        raise RuntimeError(f"Ingestion failed: {str(e)}") from e
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)