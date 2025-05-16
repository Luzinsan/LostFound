## Before running celery, ensure that redis (broker) is started:
# sudo systemctl enable redis
# sudo systemctl start redis
## And check it:
# sudo systemctl status redis 

# running celery workers
uv run celery -A celery_app worker --loglevel=info
