from celery import Celery
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.configs.config import settings

app = Celery('lost_found',
             broker=settings.BROKER_URL,
             backend=settings.RESULT_BACKEND)

app.conf.update(
    broker_connection_retry_on_startup=True,
    imports=['src.core.parsers.tasks', 'src.core.indexing_search.tasks', 'src.core.semantic_search.tasks']
) 