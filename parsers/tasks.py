import logging
from celery import Celery, group
from parsers.scraper import WebScraper
from parsers import wikipedia_parser, google_places
from config import settings
import time
from utils.mongodb_handler import mongo_manager
from celery_app import app


@app.task
def parse_city_task(city: str) -> dict:
    """
    Celery task to parse data for a city and store it in MongoDB.
    """
    logging.info(f"Starting parsing task for city: {city}")
    result = group(parse_wikipedia_task.s(city), 
                 parse_google_places_task.s(city)).apply_async()
    return result.join(disable_sync_subtasks=False)


@app.task
def parse_wikipedia_task(city: str) -> dict:
    """
    Task to parse only Wikipedia data for a given city.
    """
    logging.info(f"[Task] Starting Wikipedia parsing for city: {city}")
    return wikipedia_parser.WikipediaParser()\
        .parse(city)


@app.task
def parse_google_places_task(city: str) -> dict:
    """
    Celery task to parse Google Places data for all types of places in the given city.
    Iterates over all place types defined in settings.PLACE_TYPES
    and saves the data to MongoDB.
    """
    logging.info(f"[Task] Starting Google Places parsing for city: {city} for all types")
    result = group(parse_place_by_type_task.s(city, included_type) 
                    for included_type 
                    in settings.PLACE_TYPES).apply_async()
    return result.join(disable_sync_subtasks=False)


@app.task
def parse_place_by_type_task(city: str, included_type: str) -> dict:
    """
    Task to parse place of a specific type (e.g., "restaurant") in a given city.
    """
    logging.info(f"[Task] Starting extra places parsing for city: {city}, type: {included_type}")
    return google_places.GooglePlacesParser(
            api_key=settings.GOOGLE_PLACES_API)\
        .parse(city, included_type)



@app.task
def parse_web_scrape_task(url: str) -> dict:
    """
    Task to parse website information about place in a given url.
    """
    logging.info(f"[Task] Starting website information parsing for url: {url}")
    return WebScraper().parse(url)

@app.task
def update_place_description_task(description, data: dict) -> dict:
    data["description"] = description if description else ''
    data['timestamp_scraping'] = time.time()
    data['search_text'] = google_places.GooglePlacesParser(
            api_key=settings.GOOGLE_PLACES_API)\
                .generate_search_text(data)
    mongo_manager.save(data, "places")
    return data