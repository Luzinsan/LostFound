import json
import os
import logging
import requests
from typing import Optional, List, Dict, Any

from parsers.base_parser import BaseParser
from parsers.wikipedia_parser import WikipediaParser
from utils.file_utils import normalize_filename
from config import BASE_CHECKPOINT_DIR, USER_AGENT, LANGUAGE


class OpenTripMapParser(BaseParser):
    """
    OpentripmapParser uses the OpenTripMap API to fetch attractions for a given place.
    It dynamically determines the search radius using OpenStreetMap data.
    It performs the following steps:
      1. Retrieves the city's coordinates using /places/geoname.
      2. Fetches city boundary from OpenStreetMap using Overpass API.
      3. Calculates an approximate radius from the OSM boundary (using bounds).
      4. Searches for attractions in the calculated radius using /places/radius.
      5. For each attraction, fetches detailed information using /places/xid/{xid}.
      6. Uses WikipediaParser to fetch and add/update Wikipedia descriptions for each attraction.
      7. Will use Google Places API (further) (API key already in the conf.py)
    """
    def __init__(self, api_key: str, base_url: str = "https://api.opentripmap.com/0.1/ru/places", timeout: int = 25):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.wiki_parser = WikipediaParser(user_agent=USER_AGENT, language=LANGUAGE)
        self.overpass_url = "http://overpass-api.de/api/interpreter" # Overpass API endpoint

    def _get_city_boundary_osm(self, city_name: str) -> Optional[Dict[str, float]]:
        """
        Fetches the boundary bounds of a city from OpenStreetMap using Overpass API.
        Uses relation[place~"city|town"][name="{city_name}"] query.
        Extracts bounds (minlat, minlon, maxlat, maxlon) from the relation.
        Returns a dictionary with bounds or None on failure.
        """
        overpass_query = f"""
        [out:json][timeout:{self.timeout}];
        relation[place~"city|town"][name="{city_name}"];
        out geom;
        """

        logging.debug(f"[Opentripmap] OSM query: {overpass_query}")

        try:
            response = requests.get(self.overpass_url, params={'data': overpass_query}, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data and "elements" in data and data["elements"]:
                for element in data["elements"]:
                    if "bounds" in element:
                        bounds = element["bounds"]
                        logging.info(f"[Opentripmap] Found boundary bounds (relation) for '{city_name}': {bounds}'")
                        return bounds
                    else:
                        logging.debug(f"[Opentripmap] Relation for '{city_name}' found, but no 'bounds' data available.")
                        return None # Relation found, but no bounds
                logging.debug(f"[Opentripmap] No relation boundary found for '{city_name}' with query: 'relation[place~\"city|town\"]...'. Not a relation or no bounds.")
            else:
                logging.debug(f"[Opentripmap] No elements found for '{city_name}' with query: 'relation[place~\"city|town\"]...'. Empty elements list.")

        except requests.exceptions.RequestException as e:
            logging.error(f"[Opentripmap] Request error for '{city_name}' with query: 'relation[place~\"city|town\"]...': {e}")
        except json.JSONDecodeError as e:
            logging.error(f"[Opentripmap] JSON decode error for '{city_name}' with query: 'relation[place~\"city|town\"]...': {e}")

        logging.warning(f"[Opentripmap] Could not fetch boundary bounds for '{city_name}' using OSM relation query.")
        return None


    def _calculate_radius_from_boundary(self, boundary_bounds: Dict[str, float]) -> Optional[int]:
        """
        Calculates an approximate radius from the city boundary bounds (minlat, minlon, maxlat, maxlon).
        Uses the bounding box diagonal as an approximation.
        Returns radius in meters, or None if calculation fails or bounds are invalid.
        """
        if not boundary_bounds:
            return None

        min_lon = boundary_bounds.get('minlon')
        max_lon = boundary_bounds.get('maxlon')
        min_lat = boundary_bounds.get('minlat')
        max_lat = boundary_bounds.get('maxlat')

        if None in [min_lon, max_lon, min_lat, max_lat]:
            logging.warning("[Opentripmap] Incomplete boundary bounds data, cannot calculate radius.")
            return None

        # Approximate diagonal in degrees (rough, for radius estimation)
        diagonal_lon = max_lon - min_lon
        diagonal_lat = max_lat - min_lat
        diagonal_degrees = max(diagonal_lon, diagonal_lat) # Take the larger dimension as a rough diagonal

        # Very rough conversion from degrees to meters (at equator, 1 degree ~ 111km)
        # This is a simplification and not geographically precise, but okay for radius approximation
        approx_diagonal_meters = diagonal_degrees * 111000
        radius_meters = approx_diagonal_meters / 2.0

        return int(radius_meters) # Return radius in meters as integer


    def parse(self, place: str, limit: int = 10000,
              checkpoint: bool = True, checkpoint_dir: str = os.path.join(BASE_CHECKPOINT_DIR, "opentripmap"),
              default_radius: int = 20000, # Default radius if OSM boundary fails
              **kwargs) -> Optional[List[Dict[str, Any]]]:
        logging.info(f"[Opentripmap] Starting parsing for place: {place}")
        aggregated_results = []

        # Step 1: Retrieve city coordinates using /places/geoname
        geoname_url = f"{self.base_url}/geoname"
        params = {
            "name": place,
            "apikey": self.api_key
        }
        try:
            response = requests.get(geoname_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            geoname_data = response.json()
            if not geoname_data.get("lat") or not geoname_data.get("lon"):
                logging.warning(f"[Opentripmap] Coordinates not found for place '{place}'.")
                return None
            lat = geoname_data["lat"]
            lon = geoname_data["lon"]
            logging.info(f"[Opentripmap] Found coordinates for '{place}': lat={lat}, lon={lon}")
        except Exception as e:
            logging.error(f"[Opentripmap] Error obtaining geoname data for '{place}': {e}")
            return None

        # Step 2 & 3: Fetch city boundary from OSM and calculate radius
        # Calculate radius dynamically if not provided explicitly
        boundary_bounds = self._get_city_boundary_osm(place) # Now returns bounds dict
        if boundary_bounds:
            radius_from_osm = self._calculate_radius_from_boundary(boundary_bounds) # Pass bounds to radius calculation
            if radius_from_osm:
                radius = radius_from_osm
                logging.info(f"[Opentripmap] Radius calculated from OSM boundary bounds for '{place}': {radius} meters")
            else:
                radius = default_radius
                logging.warning(f"[Opentripmap] Failed to calculate radius from OSM boundary bounds for '{place}'. Using default radius: {default_radius} meters.")
        else:
            radius = default_radius
            logging.warning(f"[Opentripmap] Failed to fetch OSM boundary bounds for '{place}'. Using default radius: {default_radius} meters.")
        
        # Step 4: Search for attractions within the determined radius using /places/radius
        radius_url = f"{self.base_url}/radius"
        params = {
            "radius": radius,
            "lon": lon,
            "lat": lat,
            "limit": limit,
            "apikey": self.api_key
        }
        try:
            response = requests.get(radius_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            radius_data = response.json()
            features = radius_data.get("features", [])
            if not features:
                logging.warning(f"[Opentripmap] No features found within radius for '{place}'.")
                return None
            logging.info(f"[Opentripmap] Found {len(features)} features in radius for '{place}'.")
        except Exception as e:
            logging.error(f"[Opentripmap] Error obtaining radius data for '{place}': {e}")
            return None

        # Step 5 & 6: For each attraction, get detailed info via /places/xid/{xid} and Wikipedia data
        for feature in features:
            xid = feature.get("properties", {}).get("xid")
            name = feature.get("properties", {}).get("name")
            if not xid or name=='':
                continue
            detail_url = f"{self.base_url}/xid/{xid}"
            params = {
                "apikey": self.api_key
            }
            try:
                detail_resp = requests.get(detail_url, params=params, timeout=self.timeout)
                detail_resp.raise_for_status()
                detail_data = detail_resp.json()
                if wiki_data := self.wiki_parser.parse(name, checkpoint=False):
                    detail_data["wikipedia_extracts"] = wiki_data
                    logging.info(f"[OpenTripMap] Added/Updated Wikipedia description for '{name}'")
                else:
                    logging.warning(f"[OpenTripMap] No Wikipedia page found for '{name}'")
                aggregated_results.append(detail_data)
            except Exception as e:
                logging.error(f"[Opentripmap] Error obtaining details for xid '{xid}': {e}")
                continue

        # Step 7: Save checkpoint if enabled.
        if checkpoint:
            if not os.path.exists(checkpoint_dir):
                os.makedirs(checkpoint_dir)
            cp_filename = os.path.join(checkpoint_dir, f"opentripmap_{normalize_filename(place)}.json")
            try:
                with open(cp_filename, "w", encoding="utf-8") as f:
                    json.dump(aggregated_results, f, ensure_ascii=False, indent=4)
                logging.info(f"[Opentripmap] Checkpoint saved: {cp_filename}")
            except Exception as e:
                logging.error(f"[Opentripmap] Error saving checkpoint: {e}")

        logging.info(f"[Opentripmap] Aggregated {len(aggregated_results)} detailed items for '{place}'.")
        return aggregated_results