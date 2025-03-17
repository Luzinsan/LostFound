import requests
import json
import os
from config import settings
import logging
import time
from typing import List, Dict, Any, Optional
from utils.file_utils import normalize_filename


class PlacesAPIClient:
    """
    Client for interacting with the Google Places API (New).
    Handles API requests, error handling, and retries.
    """
    BASE_URL = "https://places.googleapis.com/v1/places:searchText"
    DETAILS_BASE_URL = "https://places.googleapis.com/v1/places/"

    def __init__(self, api_key: str, language_code: str = settings.LANGUAGE_CODE, region_code: str = settings.REGION_CODE,
                 timeout: int = settings.TIMEOUT, retry_delay: int = settings.RETRY_DELAY, max_retries: int = settings.MAX_RETRIES):
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
        self.api_key = api_key
        self.language_code = language_code
        self.region_code = region_code
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        self.params = {
            "languageCode": self.language_code,
            "regionCode": self.region_code,
        }

    def _make_request(self, url: str, headers: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None,
                      method: str = "POST", retries: int = settings.MAX_RETRIES) -> Optional[Dict[str, Any]]:
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
                response = requests.post(url, headers=headers, params=params, timeout=self.timeout)
            elif method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            else:
                raise ValueError("Invalid HTTP method. Must be 'POST' or 'GET'.")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"API request error: {e}")
            if retries > 0:
                delay = self.retry_delay * (2 ** (self.max_retries - retries))  # Exponential backoff
                logging.info(f"Retrying in {delay} seconds... ({retries} retries remaining)")
                time.sleep(delay)
                return self._make_request(url, headers=headers, params=params, method=method, retries=retries - 1)
            else:
                logging.error(f"Max retries exceeded for URL: {url}")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None


    def text_search(self, query: str, included_type: Optional[str] = None,
                    included_primary_types: Optional[List[str]] = None,
                    excluded_primary_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
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
        headers["X-Goog-FieldMask"] = "places.id,places.displayName,places.location"

        params = self.params.copy()
        params.update({
            "textQuery": query,
            "maxResultCount": settings.LIMIT_RESULTS, 
        })
        if included_type:
            params["includedType"] = included_type
        if included_primary_types:
            params["includedPrimaryTypes"] = included_primary_types
        if excluded_primary_types:
            params["excludedPrimaryTypes"] = excluded_primary_types

        all_results = []
        next_page_token = None

        while True:
            if next_page_token:
                params["pageToken"] = next_page_token

            response_data = self._make_request(url, headers, params)

            if not response_data:
                break

            places = response_data.get("places", [])
            all_results.extend(places)

            next_page_token = response_data.get("nextPageToken")
            if not next_page_token:
                break

            time.sleep(1)

        return all_results


    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information about a place by its ID.

        Args:
            place_id: The ID of the place.

        Returns:
            Dictionary with detailed place information, or None on error.
        """
        url = f"{self.DETAILS_BASE_URL}{place_id}"
        headers = self.headers.copy()
        headers["X-Goog-FieldMask"] = "id,displayName,formattedAddress,websiteUri,rating,userRatingCount,reviews,regularOpeningHours,types,photos"
        return self._make_request(url, headers=headers, params=self.params, method="GET")



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

    def parse(self, city_name: str, types_to_search: List[str] = settings.PLACE_TYPES, 
              checkpoint_dir: str = os.path.join(settings.BASE_CHECKPOINT_DIR, "google_places")) -> List[Dict[str, Any]]:
        """
        Parses place information for a given city and types of places.

        Args:
            city_name: Name of the city to parse.
            types_to_search: List of place types to search for (e.g., ["restaurant", "cafe"]).

        Returns:
            List of dictionaries with detailed place information.
        """
        all_places_data = []

        for place_type in types_to_search:
            logging.info(f"Searching for {place_type} in {city_name}...")
            query = f"{place_type} в {city_name}"
            places = self.api_client.text_search(query, included_type=place_type)

            if not places:
                logging.info(f"No {place_type} found in {city_name}.")
                continue

            logging.info(f"Found {len(places)} {place_type} in {city_name}.")

            for place in places:
                place_id = place["id"]
                logging.info(f"Fetching details for place ID: {place_id}")
                place_details = self.api_client.get_place_details(place_id)

                if place_details:
                    all_places_data.append(place_details)

        if not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)
        cp_filename = os.path.join(checkpoint_dir, f"{normalize_filename(city_name)}.json")
        with open(cp_filename, "w", encoding="utf-8") as f:
            json.dump(all_places_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Results saved to {cp_filename}")

        return all_places_data