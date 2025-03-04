import os
import json
import logging
import re
from typing import Any, Dict, Optional
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
from config import AGGREGATED_DIR, PLACES
from fuzzywuzzy import fuzz


# Функция для нормализации имени места
def normalize_filename(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[\s-]+', '_', name)
    name = re.sub(r'[^\w_]', '', name)
    return name


class CompositeAggregator:
    def __init__(self,
                 wikipedia_parser,
                 otm_parser,
                 data_processor):
        self.wikipedia_parser = wikipedia_parser
        self.otm_parser = otm_parser
        self.data_processor = data_processor
        self.index = {}

    def aggregate(self, place: str,
                  flickr_max_pages: Optional[int] = None,
                  scraper_max_pages: Optional[int] = None) -> Dict[str, Any]:
        data = {"place": place}
        agg_filename = os.path.join(AGGREGATED_DIR, f"{normalize_filename(place)}.json")
        if os.path.exists(agg_filename):
            logging.info(f"[Aggregate] Data for '{place}' already exists in {agg_filename}. Skipping aggregation.")
            try:
                with open(agg_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                logging.error(f"[Aggregate] Error loading existing data for '{place}': {e}")

        # Wikipedia data
        wiki_data = self.wikipedia_parser.parse(place, checkpoint=True)
        if wiki_data:
            data["wikipedia"] = wiki_data
        else:
            data["wikipedia"] = None

        # Open Trip Map
        otm_data = self.otm_parser.parse(place, max_pages=flickr_max_pages)
        data["otm"] = otm_data if otm_data is not None else []

        # Add data to the index for fast searching
        normalized_place = normalize_filename(place)
        self.index[normalized_place] = data

        # Log normalized place name
        logging.info(f"[Indexing] Normalized place: {normalized_place} - {place}")

        # Save aggregated data into a file
        save_filename = os.path.join(AGGREGATED_DIR, f"{normalized_place}.json")
        with open(save_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"[Save] Data for '{place}' saved to {save_filename}")

        return data

    def search(self, query: str, fuzzy: bool = False) -> Optional[list]:
        query = query.lower().strip()
        results = []

        # Try to match the query directly
        for place, data in self.index.items():
            if query in place:
                results.append(data)

        # Perform fuzzy search if enabled
        if fuzzy:
            logging.info(f"Performing fuzzy search for query: {query}")
            for place, data in self.index.items():
                # Using fuzz.partial_ratio for fuzzy matching
                if fuzz.partial_ratio(query, place) > 70:  # 70% similarity threshold
                    results.append(data)

        # If no results, return None
        if not results:
            return None

        return results
