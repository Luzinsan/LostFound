import os
import json
import logging
from typing import Any, Dict, Optional, List

from config import settings
from utils.file_utils import normalize_filename, save_json
from indexing.index_manager import IndexManager
from parsers import wikipedia_parser, google_places
from managers import web_scrape_manager 

class CompositeAggregator:
    def __init__(self, 
                 wikipedia_parser: wikipedia_parser.WikipediaParser, 
                 web_scrape_manager: web_scrape_manager.WebScrapeManager):
        self.wikipedia_parser = wikipedia_parser
        self.web_scrape_manager = web_scrape_manager
        self.index_manager = IndexManager()

    def aggregate(self, place: str) -> Dict[str, Any]:
        """
        Aggregates data for a given place from various sources.
        Saves the aggregated data in a per-place JSON file.
        """
        data = {"place": place}

        wiki_data = self.wikipedia_parser.parse(place, checkpoint=True)
        data["wikipedia"] = wiki_data if wiki_data else None

        google_places_data = self.web_scrape_manager.scrape_descriptions(place)
        data["google_places"] = google_places_data if google_places_data else []

        return data

    def search(self, city_name: str, query: str) -> List[tuple]:
        """
        Delegates search to the IndexManager.
        Returns a list of tuples (name_attraction, score) sorted by descending score.
        """
        return self.index_manager.search(city_name, query)
