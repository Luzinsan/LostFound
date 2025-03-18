import requests
import json
import os
from config import settings
import logging
import time
from typing import List, Dict, Any, Optional
from utils.file_utils import normalize_filename, load_json, save_json
from parsers.scraper import WebScraper


class PlacesAPIClient:
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
        Initializes the PlacesAPIClient.

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
            "X-Goog-Api-Key": api_key
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
            return response.json()

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
    def text_search(self, 
                    query: str, 
                    included_type: Optional[str] = None,
                    included_primary_types: Optional[List[str]] = None,
                    excluded_primary_types: Optional[List[str]] = None
                    ) -> List[Dict[str, Any]]:
        """
        Performs a Text Search request to the Places API (New).

        Args:
            query: Text query (e.g., "restaurants in Moscow").
            included_type:  A single place type to include.
            included_primary_types: List of primary place types to include.
            excluded_primary_types: List of primary place types to exclude.

        Returns:
            List of dictionaries with place information.
        """
        url = self.BASE_URL
        headers = self.headers.copy()
        headers["X-Goog-FieldMask"] = settings.FIELD_MASK

        params = self.params.copy()
        params.update({
            "textQuery": query, 
        })
        if included_type:
            params["includedType"] = included_type
        if included_primary_types:
            params["includedPrimaryTypes"] = included_primary_types
        if excluded_primary_types:
            params["excludedPrimaryTypes"] = excluded_primary_types

        all_results = []
        next_page_token = None

        for n in range(self.num_pages):
            if next_page_token:
                params["pageToken"] = next_page_token

            response_data = self._make_request(url=url, 
                                               headers=headers, 
                                               params=params,
                                               method='POST')
            if not response_data: break
            all_results.extend(response_data.get("places", []))

            if not (next_page_token := response_data.get("nextPageToken")):
                break
            time.sleep(1)

        return all_results

class GooglePlacesParser:
    """
    Parses place information for a given city using the PlacesAPIClient.
    Handles fetching places of different types and saving results.
    """
    def __init__(self, api_key: str):
        """
        Initializes the PlaceParser.

        Args:
            api_client: An instance of PlacesAPIClient.
            checkpoint_dir: Directory to save checkpoint files.
        """
        self.api_client = PlacesAPIClient(api_key)

    def parse(self, 
              city_name: str, 
              types_to_search: List[str] = settings.PLACE_TYPES, 
              checkpoint_dir: str = os.path.join(settings.BASE_CHECKPOINT_DIR, "google_places")
              ) -> List[Dict[str, Any]]:
        """
        Parses place information for a given city and types of places.

        Args:
            city_name: Name of the city to parse.
            types_to_search: List of place types to search for (e.g., ["restaurant", "cafe"]).

        Returns:
            List of dictionaries with detailed place information.
        """
        os.makedirs(checkpoint_dir, exist_ok=True)
        cp_filename = os.path.join(checkpoint_dir, f"{normalize_filename(city_name)}.json")

        if os.path.exists(cp_filename):
            logging.info(f"Loading Google Places data from checkpoint: {cp_filename}")
            return load_json(cp_filename)  # Load from checkpoint

        all_places_data = []
        for place_type in types_to_search:
            logging.info(f"Searching for {place_type} in {city_name}...")
            query = f"{place_type} в {city_name}"
            places = self.api_client.text_search(query, 
                                                 included_type=place_type)

            if not places:
                logging.info(f"No {place_type} found in {city_name}.")
                continue
            all_places_data.extend(places)
            logging.info(f"Found {len(places)} {place_type} in {city_name}.")

        logging.info(f"Saving Google Places data to checkpoint: {cp_filename}")
        save_json(all_places_data, cp_filename)

        return all_places_data