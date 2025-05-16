import logging
from celery import Celery, group, shared_task
from typing import Dict, List, Optional
import time
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.core.parsers.scraper import WebScraper
from src.core.parsers import wikipedia_parser, google_places
from src.core.celery_app import app
from src.configs.config import settings
from src.utils.mongodb_handler import mongo_manager


@app.task
def parse_city_task(city: str, place_types: Optional[List[str]] = None) -> dict:
    """
    Celery task to parse data for a city and store it in MongoDB.
    
    Args:
        city: City name to parse
        place_types: Optional list of place types to parse. If None, uses all types from settings.
    """
    logging.info(f"Starting parsing task for city: {city}")
    result = group(parse_wikipedia_task.s(city), 
                 parse_google_places_task.s(city, place_types)).apply_async()
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
def parse_google_places_task(city: str, place_types: Optional[List[str]] = None) -> dict:
    """
    Celery task to parse Google Places data for specified types of places in the given city.
    
    Args:
        city: City name to parse
        place_types: Optional list of place types to parse. If None, uses all types from settings.PLACE_TYPES
    """
    # Use all place types from settings if not specified
    types_to_parse = place_types if place_types else settings.PLACE_TYPES
    
    logging.info(f"[Task] Starting Google Places parsing for city: {city} for types: {types_to_parse}")
    result = group(parse_place_by_type_task.s(city, included_type) 
                    for included_type 
                    in types_to_parse).apply_async()
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
def update_place_description_task(description: str, data: dict) -> dict:
    """
    Updates the place description.
    """
    data["description"] = description if description else ''
    data['timestamp_scraping'] = time.time()
    data['search_text'] = google_places.GooglePlacesParser(
            api_key=settings.GOOGLE_PLACES_API)\
                .generate_search_text(data)
    mongo_manager.save(data, "places")
    return data
