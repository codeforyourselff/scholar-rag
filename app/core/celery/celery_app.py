from celery import Celery
from app.config import CeleryAppSettings, Settings, get_settings

settings: Settings = get_settings()
celery_settings: CeleryAppSettings = settings.celery
celery : Celery = Celery("scholar_rag_worker",broker=celery_settings.broker_url,backend=celery_settings.result_backend,include=["app.workers.ingestion_worker"])
celery.conf.update(celery_settings.model_dump())