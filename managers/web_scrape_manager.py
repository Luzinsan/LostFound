import os
import logging
import time
from typing import List, Dict, Any
from config import settings
from parsers.google_places import GooglePlacesParser
from parsers.scraper import WebScraper
from utils.file_utils import normalize_filename, load_json, save_json

class WebScrapeManager:
    def __init__(self, google_places_parser: GooglePlacesParser):
        self.google_places_parser = google_places_parser
        self.scraper = WebScraper()
        self.scraped_data_dir = os.path.join(settings.BASE_CHECKPOINT_DIR, "google_places_scraped")

    def scrape_descriptions(self, city_name: str):
        """
        Loads Google Places data, scrapes descriptions, and saves updated data.
        """
        os.makedirs(self.scraped_data_dir, exist_ok=True)
        google_places_data = self.google_places_parser.parse(city_name)  # Load/fetch Google Places
        if not google_places_data:
            logging.info(f"No Google Places data found for {city_name}.")
            return

        scraped_filename = os.path.join(self.scraped_data_dir, f"{normalize_filename(city_name)}.json")
        if os.path.exists(scraped_filename):
            logging.info(f"Loading web scraped data from {scraped_filename}")
            all_places_data = load_json(scraped_filename)
        else:
            all_places_data = google_places_data
        logging.info(f"Web scraping descriptions for {city_name}...")

        updated_count = 0
        for place in all_places_data:
            website_uri = place.get("websiteUri")
            if website_uri and "description" not in place:
                logging.info(f"Scraping {website_uri}...")
                try:
                    description = self.scraper.parse_website(website_uri)
                    if description:
                        place["description"] = description
                        updated_count += 1
                except Exception as e:
                    logging.error(f"Error during scraping {website_uri}: {e}")
                time.sleep(5)

        logging.info(f"Scraped descriptions for {updated_count} places in {city_name}.")
        save_json(all_places_data, scraped_filename, 'id', 'mongodb://localhost:27017/', 'lost_found', 'place')
        return all_places_data