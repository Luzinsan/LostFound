import json
import os
import logging
import requests
from typing import Optional, List, Dict, Any

from parsers.base_parser import BaseParser
from utils.file_utils import normalize_filename
from config import BASE_CHECKPOINT_DIR


class OpenTripMapParser(BaseParser):
    """
    OpentripmapParser uses the OpenTripMap API to fetch attractions for a given place.
    It performs the following steps:
      1. Retrieves the city's coordinates using /places/geoname.
      2. Searches for attractions in the specified radius using /places/radius.
      3. For each attraction, fetches detailed information using /places/xid/{xid}.
      4. Will use Google Places API (further) (API key already in the conf.py)
    """
    def __init__(self, api_key: str, base_url: str = "https://api.opentripmap.com/0.1/ru/places", timeout: int = 25):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout


    def parse(self, place: str, radius: int = 10000, limit: int = 50,
              checkpoint: bool = True, checkpoint_dir: str = os.path.join(BASE_CHECKPOINT_DIR, "opentripmap"),
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

        # Step 2: Search for attractions within a given radius using /places/radius
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

        # Step 3: For each attraction, get detailed info via /places/xid/{xid}
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
                aggregated_results.append(detail_data)
            except Exception as e:
                logging.error(f"[Opentripmap] Error obtaining details for xid '{xid}': {e}")
                continue

        # Save checkpoint if enabled.
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

