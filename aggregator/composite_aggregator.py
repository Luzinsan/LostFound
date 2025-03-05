import os
import json
import logging
from typing import Any, Dict, Optional, List

from config import AGGREGATED_DIR, PLACES
from utils.file_utils import normalize_filename
from indexing.index_manager import IndexManager

class CompositeAggregator:
    def __init__(self, wikipedia_parser, otm_parser, data_processor):
        self.wikipedia_parser = wikipedia_parser
        self.otm_parser = otm_parser
        self.data_processor = data_processor
        self.index_manager = IndexManager()  # IndexManager now handles indexing logic
        self.index = {}  # Aggregated data storage

    def aggregate(self, place: str, force_parse: bool = False) -> Dict[str, Any]:
        """
        Aggregates data for a given place from various sources.
        Saves the aggregated data in a per-place JSON file.
        """
        data = {"place": place}
        agg_filename = os.path.join(AGGREGATED_DIR, f"{normalize_filename(place)}.json")
        normalized_place = normalize_filename(place)

        if not force_parse and os.path.exists(agg_filename):
            logging.info(f"[Aggregate] Loading existing data for '{place}' from {agg_filename}")
            try:
                with open(agg_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.index[normalized_place] = data
                return data
            except Exception as e:
                logging.error(f"[Aggregate] Error loading data for '{place}': {e}")

        # Parse new data from sources
        wiki_data = self.wikipedia_parser.parse(place, checkpoint=True)
        data["wikipedia"] = wiki_data if wiki_data else None

        otm_data = self.otm_parser.parse(place)
        data["otm"] = otm_data if otm_data else []

        self.index[normalized_place] = data

        # Save aggregated data to file
        try:
            with open(agg_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logging.info(f"[Aggregate] Data for '{place}' saved to {agg_filename}")
        except Exception as e:
            logging.error(f"[Aggregate] Error saving data for '{place}': {e}")
        return data

    def search(self, query: str) -> List[tuple]:
        """
        Delegates search to the IndexManager.
        Returns a list of tuples (doc_id, score) sorted by descending score.
        """
        return self.index_manager.search(query)
