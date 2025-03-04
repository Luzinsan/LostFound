# parsers/web_scraper_parser.py

import json
import os
import logging
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser
from utils.file_utils import normalize_filename
from config import BASE_CHECKPOINT_DIR

class WebScraperParser(BaseParser):
    def __init__(self, user_agent: Optional[str] = None, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36")
        })
        self.timeout = timeout

    def parse(self, place: str, css_selector: str, next_page_selector: Optional[str] = None,
              max_pages: Optional[int] = None, checkpoint: bool = True, checkpoint_dir: str = os.path.join(BASE_CHECKPOINT_DIR, "scraper"), **kwargs) -> Optional[List[Dict[str, Optional[str]]]]:
        base_url = f"https://www.lonelyplanet.com/search?q={place}"
        logging.info(f"[Scraper] Starting scraping for '{place}' from {base_url}")
        aggregated_results = []
        current_url = base_url
        page_count = 0

        while current_url:
            from main import STOP_FLAG
            if STOP_FLAG:
                logging.info("[Scraper] Stop flag detected. Exiting scraper loop.")
                break

            page_count += 1
            logging.info(f"[Scraper] Processing page {page_count}: {current_url}")
            try:
                response = self.session.get(current_url, timeout=self.timeout)
                response.raise_for_status()
            except requests.RequestException as re:
                logging.error(f"[Scraper] Error fetching {current_url}: {re}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            elements = soup.select(css_selector)
            logging.info(f"[Scraper] Found {len(elements)} elements on page {page_count}")
            for element in elements:
                text = element.get_text(strip=True)
                link = element.get("href")
                aggregated_results.append({
                    "text": text,
                    "link": link
                })
            cp_filename = os.path.join(checkpoint_dir, f"scraper_{normalize_filename(place)}_page_{page_count}.json")
            with open(cp_filename, "w", encoding="utf-8") as f:
                json.dump(aggregated_results, f, ensure_ascii=False, indent=4)
            logging.info(f"[Scraper] Checkpoint saved: {cp_filename}")
            if max_pages is not None and page_count >= max_pages:
                logging.info(f"[Scraper] Reached max_pages limit: {max_pages}.")
                break
            if next_page_selector:
                next_page_element = soup.select_one(next_page_selector)
                if next_page_element and next_page_element.get("href"):
                    next_href = next_page_element.get("href")
                    current_url = urljoin(current_url, next_href)
                    logging.info(f"[Scraper] Next page: {current_url}")
                else:
                    logging.info("[Scraper] No next page link found. Ending pagination.")
                    break
            else:
                break

        logging.info(f"[Scraper] Aggregated {len(aggregated_results)} items for '{place}'.")
        return aggregated_results if aggregated_results else None
