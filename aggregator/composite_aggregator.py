# aggregator/composite_aggregator.py

import json
import os
import logging
from typing import Any, Dict, Optional
from utils.file_utils import normalize_filename
from config import AGGREGATED_DIR

class CompositeAggregator:
    def __init__(self,
                 wikipedia_parser,
                 otm_parser,
                #  scraper_parser,
                #  osm_parser,
                 data_processor):
        self.wikipedia_parser = wikipedia_parser
        self.otm_parser = otm_parser
        # self.scraper_parser = scraper_parser
        # self.osm_parser = osm_parser
        self.data_processor = data_processor

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
            # interesting_facts = self.data_processor.process_text(wiki_data.get("summary", ""))
            # data["interesting_facts"] = interesting_facts
        else:
            data["wikipedia"] = None
            # data["interesting_facts"] = []
        
        # Open Trip Map
        otm_data = self.otm_parser.parse(place, max_pages=flickr_max_pages)
        data["otm"] = otm_data if otm_data is not None else []
        
        # Web Scraper data (e.g., LonelyPlanet)
        # css_selector = "a.card-link"  # Adjust these selectors as needed.
        # next_page_selector = "a.pagination__next"
        # scraper_data = self.scraper_parser.parse(place, css_selector=css_selector,
        #                                          next_page_selector=next_page_selector,
        #                                          max_pages=scraper_max_pages)
        # data["travel_info"] = scraper_data if scraper_data is not None else []
        
        # OSM data (Overpass API)
        # osm_data = self.osm_parser.parse(place)
        # data["osm"] = osm_data if osm_data is not None else []

        return data


