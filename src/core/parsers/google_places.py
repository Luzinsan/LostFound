import requests
import json
import logging
import time
from typing import List, Dict, Any, Optional
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
from src.core.parsers import tasks
from src.configs.config import settings
from src.utils.mongodb_handler import mongo_manager
from src.core.parsers.base_parser import BaseParser


class GooglePlacesParser(BaseParser):
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
            "X-Goog-FieldMask": settings.FIELD_MASK + ',' + settings.BOOLEAN_FIELDS \
                if settings.BOOLEAN_FIELDS \
                else settings.FIELD_MASK
        }
        self.params = {
            "languageCode": language_code,
            "regionCode": region_code,
            "pageSize": results_per_page,
        }
        self.api_key = api_key

    def _make_request(self, 
                      url: str, 
                      headers: Optional[Dict[str, Any]] = None, 
                      params: Optional[Dict[str, Any]] = None,
                      method: str = "POST",
                      retries=2
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
            if retries > 0:
                delay = self.retry_delay * (2 ** (self.max_retries - retries))  # Exponential backoff
                logging.info(f"Retrying in {delay} seconds... ({retries} retries remaining)")
                time.sleep(delay)
                return self._make_request(url, 
                                          headers=headers, 
                                          params=params, 
                                          method=method, 
                                          retries=retries - 1)
            else:
                logging.error(f"Max retries exceeded for URL: {url}")
                return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
    
    def generate_search_text(self, data: Dict[str, Any]) -> str:
        try:
            def process_value(attr: str, value: Any) -> str:
                try:
                    if value is None:
                        return ''
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, bool) and value==True:
                        return attr
                    elif not isinstance(value,bool) and isinstance(value, (int, float)):
                        return f'{attr}_{value}'
                    elif isinstance(value, list) and (attr=='types'):
                        return ' '.join(str(v) for v in value if v is not None)
                    else:
                        return ''
                except Exception as e:
                    logging.error(f"Error processing value for attribute {attr}: {e}")
                    return ''

            search_terms = []
            priority_fields = ['displayName','primaryTypeDisplayName', 'editorialSummary', 
                                'types', 'rating', 'description']
            try:
                for field in priority_fields:
                    if field in data:
                        search_terms.append(process_value(field, data[field]))
            except Exception as e:
                logging.error(f"Error processing priority fields: {e}")

            try:
                for attr, value in data.items():
                    if not \
                        (attr in priority_fields 
                         or attr.startswith('_') 
                         or attr in {'id', 'timestamp_response','websiteUri','googleMapsUri','reviews','reviews_flattened','photos','timestamp_scraping'}):
                        search_terms.append(process_value(attr, value))
            except Exception as e:
                logging.error(f"Error processing additional fields: {e}")
                        
            return self.clean_string(' '.join(search_terms))
        except Exception as e:
            logging.error(f"Error in generate_search_text: {e}")
            return ''


    def process_reviews_for_embeddings(self, reviews: List[Dict]) -> str:
        try:
            texts = []
            for review in reviews:
                try:
                    texts.append(f"{review.get('relativePublishTimeDescription', '')} " \
                               + f"rating_{review.get('rating', '')} " \
                               + f"{review.get('text', {}).get('text', '')}\n")
                except Exception as e:
                    logging.error(f"Error processing review: {e}")
                    continue
            return self.clean_string(' '.join(texts))
        except Exception as e:
            logging.error(f"Error in process_reviews_for_embeddings: {e}")
            return ''

    def fetch_place_photos(self, place: Dict[str, Any], limit: int = 10) -> Dict[str, str]:
        """
        Fetches photos for a place from Google Places API.
        
        Args:
            place: Place data containing photo references.
            limit: Maximum number of photos to fetch, defaults to 10.
            
        Returns:
            Dictionary mapping photo index to photo URI.
        """
        try:
            if 'photos' not in place or not place['photos']:
                logging.info(f"No photos found for place: {place.get('_id', 'unknown')}")
                return {}
            
            photo_urls = []
            photo_count = min(limit, len(place['photos']))
            
            for i in range(photo_count):
                try:
                    photo_ref = place['photos'][i].get('name')
                    if not photo_ref:
                        continue
                    time.sleep(1.5)
                    
                    # Get photo URI with skipHttpRedirect
                    photo_url = f"https://places.googleapis.com/v1/{photo_ref}/media"
                    photo_params = {
                        'skipHttpRedirect': 'true',
                        'maxHeightPx': 1000,
                        'maxWidthPx': 1000,
                        'key': self.api_key
                    }
                    
                    photo_response = requests.get(
                        url=photo_url,
                        params=photo_params,
                        timeout=self.timeout
                    )
                    
                    if photo_response.status_code == 200:
                        photo_data = photo_response.json()
                        if 'photoUri' in photo_data:
                            photo_urls.append(photo_data['photoUri'])
                    else:
                        logging.error(f"Failed to fetch photo {i} for place {place.get('_id')}: {photo_response.status_code}")
                
                except Exception as e:
                    logging.error(f"Error fetching photo {i} for place {place.get('_id')}: {e}")
                    continue
                    
            return photo_urls
            
        except Exception as e:
            logging.error(f"Error in fetch_place_photos: {e}")
            return {}

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
        new_place_ids = []
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
            for place in places_data_per_page:
                place['_id'] = place.pop('id')
                place['city'] = city
                for field in ['displayName','editorialSummary','primaryTypeDisplayName','priceRange']:
                    if field in place.keys():
                        if field == 'priceRange':
                            place[field] = ('startPrice_' \
                                            + place[field].get('startPrice', {})\
                                                            .get('currencyCode', '') \
                                        + '_' + place[field].get('startPrice', {})\
                                                            .get('units', '') \
                                            if 'startPrice' in place[field].keys() else '') \
                                        + (' endPrice_' \
                                            + place[field].get('endPrice', {})\
                                                            .get('currencyCode', '') \
                                        + '_' + place[field].get('endPrice', {})\
                                                            .get('units', '') \
                                            if 'endPrice' in place[field].keys() else '')
                        else:
                            place[field] = place[field].get('text', None) 
                if place.get('reviews', None):
                    place['reviews_flattened'] = self.process_reviews_for_embeddings(place['reviews'])
                
                if place.get('photos', None):
                    place['photos'] = self.fetch_place_photos(place)

            mongo_manager.save(places_data_per_page, "places")
            for place in places_data_per_page:
                new_place_ids.append(place["_id"])
                if "description" not in place:
                    if (website_uri := place.get("websiteUri"))  :
                        logging.info(f"Scraping {website_uri}...")
                        try:
                            tasks.parse_web_scrape_task\
                                .apply_async(args=[website_uri], 
                                            link=tasks.update_place_description_task.s(place))
                        except Exception as e:
                            logging.error(f"Error during scraping {website_uri}: {e}")
                    else:
                        logging.info(f"No websiteUri for {place['displayName']}")
                        tasks.update_place_description_task.s(None, place).apply_async()
            all_places_data.extend(places_data_per_page)
            if not (next_page_token := response.get("nextPageToken")):
                break
            time.sleep(1)
        mongo_manager.update_city_places(city, new_place_ids)
        return all_places_data
    