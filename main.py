import os
import sys
import logging
import signal
import time
import config
from aggregator.composite_aggregator import CompositeAggregator
from parsers.wikipedia_parser import WikipediaParser
from parsers.open_trip_map_parser import OpenTripMapParser
from data_processing.data_processor import DataProcessor
from utils.file_utils import save_json, load_json, normalize_filename

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Global flag for graceful termination
STOP_FLAG = False

def signal_handler(sig, frame):
    global STOP_FLAG
    logging.info("Received stop signal. Exiting after current checkpoint...")
    STOP_FLAG = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Create directories for checkpoints and aggregated data if they do not exist
for resource in config.RESOURCES:
    dir_path = os.path.join(config.BASE_CHECKPOINT_DIR, resource)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
if not os.path.exists(config.AGGREGATED_DIR):
    os.makedirs(config.AGGREGATED_DIR)

def main():
    # Check for '--load-only' flag to bypass re-parsing
    load_only = '--load-only' in sys.argv
    load_only = True
    aggregated_filename = os.path.join(config.AGGREGATED_DIR, "all_places_aggregated.json")
    all_data = {}

    if load_only:
        if os.path.exists(aggregated_filename):
            all_data = load_json(aggregated_filename)
            logging.info(f"[Main] Loaded aggregated data from {aggregated_filename}")
        else:
            logging.error(f"[Main] Aggregated file {aggregated_filename} not found. Exiting.")
            return
    else:
        # Initialize parsers and data processor
        wiki_parser = WikipediaParser(user_agent=config.USER_AGENT, language=config.LANGUAGE)
        otm_parser = OpenTripMapParser(api_key=config.OPENTRIPMAP_API_KEY)
        data_processor = DataProcessor(config.KEYWORDS)

        aggregator = CompositeAggregator(
            wikipedia_parser=wiki_parser,
            otm_parser=otm_parser,
            data_processor=data_processor
        )

        # Aggregate data for each place in config.PLACES
        for place in config.PLACES:
            if STOP_FLAG:
                logging.info("Stop flag detected. Exiting before processing next place.")
                break
            logging.info(f"[Aggregate] Aggregating data for: {place}")
            data = aggregator.aggregate(place)
            agg_filename = os.path.join(config.AGGREGATED_DIR, f"{normalize_filename(place)}.json")
            save_json(data, agg_filename)
            all_data[place] = data
            time.sleep(2)
        save_json(all_data, aggregated_filename)
        logging.info(f"[Aggregate] All data aggregated and saved to {aggregated_filename}")

    # Build the search index
    wiki_parser = WikipediaParser(user_agent=config.USER_AGENT, language=config.LANGUAGE)
    otm_parser = OpenTripMapParser(api_key=config.OPENTRIPMAP_API_KEY)
    data_processor = DataProcessor(config.KEYWORDS)
    aggregator = CompositeAggregator(
        wikipedia_parser=wiki_parser,
        otm_parser=otm_parser,
        data_processor=data_processor
    )
    # Populate aggregator.index from loaded aggregated data
    aggregator.index = {normalize_filename(place): data for place, data in all_data.items()}
    aggregator.index_manager.build_and_save_index(aggregator.index)

    # Search stage: perform search on the built index
    search_flag = True
    while search_flag:
        print("\nSearch in aggregated data:")
        query = input("Enter search query: ")
        results = aggregator.search(query)
        if results:
            print("Search results:")
            for doc_id, score in results:
                print(f"{doc_id}: {score:.2f}")
        else:
            print("No results found.")
        search_flag = input("Try again? (Y/N):\t").lower() in ['y', 'yes', 'д', '\n']

if __name__ == '__main__':
    main()
