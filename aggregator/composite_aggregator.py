import os
import json
import logging
from typing import Any, Dict, Optional, List

from config import settings
from utils.file_utils import normalize_filename
from indexing.index_manager import IndexManager
from parsers import wikipedia_parser, google_places

class CompositeAggregator:
    def __init__(self, 
                 wikipedia_parser: wikipedia_parser.WikipediaParser, 
                 google_places_parser: google_places.GooglePlacesParser):
        self.wikipedia_parser = wikipedia_parser
        self.google_places_parser = google_places_parser
        self.index_manager = IndexManager()  # IndexManager now handles indexing logic
        self.index = {}  # Aggregated data storage

    def aggregate(self, place: str) -> Dict[str, Any]:
        """
        Aggregates data for a given place from various sources.
        Saves the aggregated data in a per-place JSON file.
        """
        data = {"place": place}
        agg_filename = os.path.join(settings.AGGREGATED_DIR, f"{normalize_filename(place)}.json")
        normalized_place = normalize_filename(place)

        # Parse new data from sources
        wiki_data = self.wikipedia_parser.parse(place, checkpoint=True)
        data["wikipedia"] = wiki_data if wiki_data else None

        google_places_data = self.google_places_parser.parse(place)
        data["google_places"] = google_places_data if google_places_data else []

        self.index[normalized_place] = data

        # Save aggregated data to file
        try:
            with open(agg_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"[Aggregate] Data for '{place}' saved to {agg_filename}")
        except Exception as e:
            logging.error(f"[Aggregate] Error saving data for '{place}': {e}")
        return data

    def search(self, city_name: str, query: str) -> List[tuple]:
        """
        Delegates search to the IndexManager.
        Returns a list of tuples (name_attraction, score) sorted by descending score.
        """
        return self.index_manager.search(city_name, query)
