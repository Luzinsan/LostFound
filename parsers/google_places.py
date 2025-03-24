import requests
import json
from config import settings
import logging
import time
from typing import List, Dict, Any, Optional
from parsers import tasks
from utils.mongodb_handler import mongo_manager


class GooglePlacesParser:
    """
    Client for interacting with the Google Places API (New).
    Handles API requests, error handling, and retries.
    """
    BASE_URL = "https://places.googleapis.com/v1/places:searchText"
    DETAILS_BASE_URL = "https://places.googleapis.com/v1/places/"

    def __init__(self, 
                 api_key: str, 
                 language_code: str = settings.LANGUAGE_CODE, 
                 region_code: str = settings.REGION_CODE,
                 timeout: int = settings.TIMEOUT, 
                 retry_delay: int = settings.RETRY_DELAY, 
                 max_retries: int = settings.MAX_RETRIES,
                 num_pages: int = settings.NUM_PAGES, 
                 results_per_page: int = settings.RESULTS_PER_PAGE):
        """
        Initializes the GooglePlacesParser.

        Args:
            api_key: Google Places API key.
            language_code: Language code for API requests.
            region_code: Region code for API requests.
            timeout: Timeout for API requests in seconds.
            retry_delay: Initial delay for retries in seconds.
            max_retries: Maximum number of retries for API requests.
        """
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.num_pages = num_pages
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": settings.FIELD_MASK
        }
        self.params = {
            "languageCode": language_code,
            "regionCode": region_code,
            "pageSize": results_per_page,
        }

    def _make_request(self, 
                      url: str, 
                      headers: Optional[Dict[str, Any]] = None, 
                      params: Optional[Dict[str, Any]] = None,
                      method: str = "POST"
                      ) -> Optional[Dict[str, Any]]:
        """
        Makes an HTTP request with error handling and retries.

        Args:
            url: The URL to request.
            data: Data for POST requests (JSON).
            method: HTTP method ("POST" or "GET").
            retries: Number of remaining retries.

        Returns:
            Dictionary with response data (JSON) or None on error.
        """
        try:
            if method == "POST":
                response = requests.post(url, 
                                         headers=headers, 
                                         params=params, 
                                         timeout=self.timeout)
            elif method == "GET":
                response = requests.get(url, 
                                        headers=headers, 
                                        params=params, 
                                        timeout=self.timeout)
            else:
                raise ValueError("Invalid HTTP method. Must be 'POST' or 'GET'.")

            response.raise_for_status()
            response = response.json()
            response.update({'timestamp_response': time.time()})
            return response

        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {e}")
            if self.retries > 0:
                delay = self.retry_delay * (2 ** (self.max_retries - self.retries))  # Exponential backoff
                logging.info(f"Retrying in {delay} seconds... ({self.retries} retries remaining)")
                time.sleep(delay)
                return self._make_request(url, 
                                          headers=headers, 
                                          params=params, 
                                          method=method, 
                                          retries=self.retries - 1)
            else:
                logging.error(f"Max retries exceeded for URL: {url}")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None


    # https://developers.google.com/maps/documentation/places/web-service/text-search
    def parse(self, 
              city: str, 
              included_type: Optional[str]
              ) -> List[Dict[str, Any]]:
        """
        Performs a Text Search request to the Places API (New).

        Args:
            city: city (e.g., "Moscow").
            included_type:  A single place type to include.

        Returns:
            List of dictionaries with place information.
        """
        params = self.params.copy()
        params.update({
            "textQuery": f"{included_type} в {city}", 
            "includedType": included_type
        })
        all_places_data = []
        next_page_token = None
        for _ in range(self.num_pages):
            if next_page_token:
                params["pageToken"] = next_page_token
            if  not (response := self._make_request(
                                        url=self.BASE_URL, 
                                        headers=self.headers, 
                                        params=params,
                                        method='POST')) \
                or not (places_data_per_page := response.get("places", [])): 
                break
            mongo_manager.save(places_data_per_page, "places")
            for place in places_data_per_page:
                if (website_uri := place.get("websiteUri")) and "description" not in place:
                    logging.info(f"Scraping {website_uri}...")
                    try:
                        tasks.parse_web_scrape_task\
                            .apply_async(args=[website_uri], 
                                         link=tasks.update_place_description_task.s(place))
                    except Exception as e:
                        logging.error(f"Error during scraping {website_uri}: {e}")
            all_places_data.extend(places_data_per_page)
            if not (next_page_token := response.get("nextPageToken")):
                break
            time.sleep(1)
        return all_places_data
    