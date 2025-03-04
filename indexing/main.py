import os
import json
import logging
import signal
import sys
import time
import re
from fuzzywuzzy import fuzz
from aggregator.composite_aggregator import CompositeAggregator
from config import PLACES, KEYWORDS, BASE_CHECKPOINT_DIR, AGGREGATED_DIR, RESOURCES, USER_AGENT, LANGUAGE, OPENTRIPMAP_API_KEY
from parsers.wikipedia_parser import WikipediaParser
from parsers.open_trip_map_parser import OpenTripMapParser
from data_processing.data_processor import DataProcessor
from utils.file_utils import save_json
from aggregator.composite_aggregator import normalize_filename
# Configure logging with timestamps and log levels.
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Global flag for graceful stop
STOP_FLAG = False


def signal_handler(sig, frame):
    global STOP_FLAG
    logging.info("Received stop signal. Preparing to exit after current checkpoint...")
    STOP_FLAG = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Create directories for checkpoints and aggregated data
for resource in RESOURCES:
    dir_path = os.path.join(BASE_CHECKPOINT_DIR, resource)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
if not os.path.exists(AGGREGATED_DIR):
    os.makedirs(AGGREGATED_DIR)


def main():
    wiki_parser = WikipediaParser(user_agent=USER_AGENT, language=LANGUAGE)
    otm_parser = OpenTripMapParser(api_key=OPENTRIPMAP_API_KEY)
    data_processor = DataProcessor(KEYWORDS)

    # Initialize CompositeAggregator with necessary parsers
    aggregator = CompositeAggregator(
        wikipedia_parser=wiki_parser,
        otm_parser=otm_parser,
        data_processor=data_processor
    )

    flickr_max_pages = 10
    scraper_max_pages = 10

    all_data = {}
    for place in PLACES:
        if STOP_FLAG:
            logging.info("Stop flag detected in main loop. Exiting before processing next place.")
            break
        logging.info(f"[Aggregate] Aggregating data for: {place}")
        data = aggregator.aggregate(place, flickr_max_pages=flickr_max_pages, scraper_max_pages=scraper_max_pages)
        agg_filename = os.path.join(AGGREGATED_DIR, f"{normalize_filename(place)}.json")
        save_json(data, agg_filename)
        all_data[place] = data
        time.sleep(2)

    aggregated_filename = os.path.join(AGGREGATED_DIR, "all_places_aggregated.json")
    save_json(all_data, aggregated_filename)
    logging.info(f"[Aggregate] All data aggregated and saved to {aggregated_filename}")

    # Start search functionality after data aggregation
    print("\nПоиск по данным:")
    query = input("Введите запрос для поиска: ")
    fuzzy_search = input("Использовать нечеткий поиск (Y/N)? ").strip().lower() == 'y'
    results = aggregator.search(query, fuzzy=fuzzy_search)

    if results:
        print("Результаты поиска:")
        for place in results:
            print(place)
    else:
        print("Ничего не найдено.")


if __name__ == '__main__':
    main()

