from celery import Celery
from config import settings

# Create the main Celery app
app = Celery('lost_found',
             broker=settings.BROKER_URL,
             backend=settings.RESULT_BACKEND)

# Configure Celery
app.conf.update(
    broker_connection_retry_on_startup=True,
    imports=['parsers.tasks', 'indexing.tasks']
) 