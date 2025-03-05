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

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

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
if not os.path.exists(os.path.join(config.AGGREGATED_DIR, "city_indexes")): # Create city_indexes dir
    os.makedirs(os.path.join(config.AGGREGATED_DIR, "city_indexes"))


def main():
    # Check for '--load-only' flag to bypass re-parsing
    load_only = '--load-only' in sys.argv
    # load_only = True # For testing load only mode
    aggregated_filename = os.path.join(config.AGGREGATED_DIR, "all_places_aggregated.json")
    all_data = {}

    wiki_parser = WikipediaParser(user_agent=config.USER_AGENT, language=config.LANGUAGE)
    otm_parser = OpenTripMapParser(api_key=config.OPENTRIPMAP_API_KEY)
    data_processor = DataProcessor(config.KEYWORDS)
    aggregator = CompositeAggregator(
        wikipedia_parser=wiki_parser,
        otm_parser=otm_parser,
        data_processor=data_processor
    )

    if load_only:
        if os.path.exists(aggregated_filename):
            all_data = load_json(aggregated_filename)
            logging.info(f"[Main] Loaded aggregated data from {aggregated_filename}")
        else:
            logging.error(f"[Main] Aggregated file {aggregated_filename} not found. Exiting.")
            return
    else:
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

    # Build the search index for each city
    for place, data in all_data.items():
        aggregator.index_manager.build_and_save_index(place, data) # Pass city name and data

    # Load indexes for all cities (for search)
    for place in config.PLACES:
        aggregator.index_manager.load_index(place)


    # Search stage: perform search on the built index
    search_flag = True # Set to True to enter search loop
    while search_flag:
        print("\nChoose a city to search in:")
        for i, city in enumerate(config.PLACES):
            print(f"{i+1}. {city}")
        city_choice_index = input("Enter city number (or 0 to exit search):\t")
        if city_choice_index == '0':
            search_flag = False
            continue

        try:
            city_index = int(city_choice_index) - 1
            if 0 <= city_index < len(config.PLACES):
                selected_city = config.PLACES[city_index]
                print(f"Searching in: {selected_city}")
                query = input("Enter search query:\t")
                results = aggregator.search(selected_city, query) # Pass city name to search
                if results:
                    print("Search results (attractions):")
                    for doc_id, score in results:
                        print(f"- {doc_id}: {score:.2f}") # doc_id is now attraction xid
                else:
                    print("No results found in this city.")
            else:
                print("Invalid city number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

        search_flag = input("Search again in another city or same? (Y/N):\t").lower() in ['y', 'yes', 'д', '\n']

if __name__ == '__main__':
    main()