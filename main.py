from config import settings
import logging
from celery import group
from parsers.tasks import parse_city_task


logging.basicConfig(level=logging.INFO if settings.DEBUG_MODE else logging.ERROR, 
                    format='%(asctime)s [%(levelname)s] %(message)s')


def main():
    task_group = group(parse_city_task.s(city) for city in settings.PLACES)
    result = task_group.apply_async()
    results = result.get()
    
if __name__ == '__main__':
    main()