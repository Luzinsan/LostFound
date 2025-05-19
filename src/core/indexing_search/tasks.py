import logging
from celery import group
import sys, os
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.utils.mongodb_handler import mongo_manager
from src.core.indexing_search.index_manager import IndexManager
from src.core.celery_app import app


@app.task
def build_location_index_task(location_id: str) -> dict:
    """
    Task to build inverted index for a specific location and store it in MongoDB.
    """
    try:
        logging.info(f"[Task] Starting index building for location: {location_id}")
        
        # Get location data from MongoDB
        location_data = mongo_manager.load({"_id": location_id}, "places")
        if not location_data or len(location_data) == 0:
            logging.error(f"No data found for location: {location_id}")
            return {"status": "error", "message": f"No data found for location: {location_id}"}
        
        location_data = location_data[0]
        city = location_data.get('city', 'unknown')
        
        # Use IndexManager to build and save index
        index_manager = IndexManager()
        index_manager.build_and_save_index(city, location_data)
        
        return {
            "status": "success",
            "message": f"Index built successfully for location: {location_id}",
        }
    except Exception as e:
        logging.error(f"Error building index for location {location_id}: {e} {type(location_data)}")
        return {"status": "error", "message": str(e)}


@app.task
def update_city_index_task(city: str, location_id: str, token_freqs: dict) -> dict:
    """
    Updates the inverted index for a city by adding or updating tokens for a location.
    """
    try:
        index_manager = IndexManager()
        if not index_manager.load_index(city):
            logging.error(f"No index found for city: {city}")
            return {"status": "error", "message": f"No index found for city: {city}"}
        
        city_index = index_manager.city_indexes[city]
        inverted_index = city_index["inverted_index"]
        doc_freq = city_index["doc_freq"]
        total_docs = city_index["total_docs"]
        
        is_new_doc = not any(location_id in postings for postings in inverted_index.values())
        if is_new_doc:
            total_docs += 1
        
        for token, freq in token_freqs.items():
            if token not in inverted_index:
                inverted_index[token] = {}
            inverted_index[token][location_id] = freq
            doc_freq[token] = len(inverted_index[token])
        
        index_manager.build_and_save_index(city, {"google_places": []}, mongo_manager)
        
        return {
            "status": "success",
            "message": f"City index updated for {city}, location {location_id}",
            "city": city
        }
    except Exception as e:
        logging.error(f"Error updating city index for {city}, location {location_id}: {e}")
        return {"status": "error", "message": str(e)}


@app.task
def build_city_locations_indices_task(city: str) -> dict:
    """
    Task to build indices for all locations in a specific city.
    """
    try:
        logging.info(f"[Task] Starting index building for all locations in city: {city}")
        
        city_data = mongo_manager.load({"city": city}, "cities")
        if not city_data or len(city_data) == 0:
            logging.error(f"No city data found for: {city}")
            return {"status": "error", "message": f"No city data found for: {city}"}
        
        place_ids = city_data[0].get('places', [])
        if not place_ids:
            logging.error(f"No place IDs found for city: {city}")
            return {"status": "error", "message": f"No place IDs found for city: {city}"}
        
        location_data = []
        for place_id in place_ids:
            place_data = mongo_manager.load({"_id": place_id}, "places")
            if place_data:
                location_data.append(place_data[0])
            else:
                logging.warning(f"No data found for place ID: {place_id}")
        
        if not location_data:
            logging.error(f"No location data found for city: {city}")
            return {"status": "error", "message": f"No location data found for city: {city}"}
        
        IndexManager().build_and_save_index(city, location_data, mongo_manager)
        
        return {
            "status": "success",
            "message": f"Index built for all locations in {city}",
        }
    except Exception as e:
        logging.error(f"Error building indices for city {city}: {e}")
        return {"status": "error", "message": str(e)}


@app.task
def build_all_indices_task(cities: Optional[List[str]] = None) -> dict:
    """
    Task to build indices for locations in specified cities or all cities if none specified.
    
    Args:
        cities: Optional list of city names. If None, processes all cities from settings.
    
    Returns:
        Dictionary with status and results from each city's index building task
    """
    try:
        cities_to_process = cities if cities else settings.CITIES
        
        logging.info(f"[Task] Starting index building for cities: {cities_to_process}")
        
        task_group = group(build_city_locations_indices_task.s(city) for city in cities_to_process)
        result = task_group.apply_async()
        results = result.join(disable_sync_subtasks=False)
        
        return {
            "status": "success",
            "message": f"Indices built for cities: {cities_to_process}",
            "cities_processed": cities_to_process,
            "results": results
        }
    except Exception as e:
        logging.error(f"Error building indices for cities {cities_to_process}: {e}")
        return {"status": "error", "message": str(e)}


@app.task
def search_index_task(city: str, query: str, limit: int = 30, types: Optional[List[str]] = None) -> dict:
    """
    Searches the inverted index for the given query within a specific city.
    Supports wildcard queries using the "*" character (e.g. "rest*" for restaurants).
    Uses TF-IDF for ranking.
    
    Args:
        city: The city to search in
        query: The search query (can include wildcards)
        limit: Maximum number of results to return
        types: Optional list of place types to filter by
        
    Returns:
        Dictionary with search results and status
    """
    try:
        logging.info(f"[Task] Searching for '{query}' in city: {city}")
        
        index_manager = IndexManager()
        if not index_manager.load_index(city, mongo_manager):
            logging.error(f"No index found for city: {city}")
            return {
                "status": "error", 
                "message": f"No index found for city: {city}",
                "results": []
            }
        
        results, query_tokens = index_manager.search(city, query)
        
        filtered_results = []
        for result in results:
            doc_id = result["doc_id"]
            
            mongo_filter = {"_id": doc_id}
            
            if types and len(types) > 0:
                mongo_filter["types"] = {"$in": types}
                
            doc_data = mongo_manager.load(mongo_filter, "places")
            
            if doc_data and len(doc_data) > 0:
                doc_data = doc_data[0]
                result.update({
                    "name": doc_data.get("displayName", {}),
                    "address": doc_data.get("shortFormattedAddress", "Unknown"),
                    "types": doc_data.get("types", []),
                    "summary": doc_data.get("editorialSummary", 'Unknown'),
                    "photos": doc_data.get("photos", None)
                })
                filtered_results.append(result)
        
        filtered_results.sort(key=lambda x: x['score'], reverse=True)
        
        limited_results = filtered_results[:limit]
        
        corrected_query = None
        if query_tokens and query_tokens != query.split():
            corrected_query = ' '.join(query_tokens)
        
        return {
            "status": "success",
            "message": f"Found {len(limited_results)} results for '{query}' in {city}",
            "results": limited_results,
            "total_found": len(filtered_results),
            "query_tokens": query_tokens if query_tokens else [],
            "wildcard_used": '*' in query,
            "corrected_query": corrected_query if corrected_query else None
        }
        
    except Exception as e:
        logging.error(f"Error searching index for '{query}' in {city}: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "results": []
        }


@app.task
def search_all_cities_task(query: str, cities: List[str] = None, limit: int = 10, types: Optional[List[str]] = None) -> dict:
    """
    Searches for the query across all specified cities (or all cities if none specified).
    
    Args:
        query: The search query (can include wildcards)
        cities: List of cities to search in (if None, all cities in settings.CITIES are used)
        limit: Maximum number of results to return per city
        types: Optional list of place types to filter by
        
    Returns:
        Dictionary with combined search results from all cities
    """
    try:
        cities = cities if cities else settings.CITIES
            
        logging.info(f"[Task] Searching for '{query}' across cities: {cities}")
        
        tasks = []
        for city in cities:
            tasks.append(search_index_task.s(city, query, limit, types))
            
        task_group = group(tasks)
        result = task_group.apply_async()
        city_results = result.join(disable_sync_subtasks=False)
        
        all_results = []
        total_found = 0
        combined_tokens = set()
        
        for city_result in city_results:
            if city_result.get("status") == "success":
                all_results.extend(city_result.get("results", []))
                total_found += city_result.get("total_found", 0)
                combined_tokens.update(city_result.get("query_tokens", []))
                
        all_results = sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)[:limit]
        
        return {
            "status": "success",
            "message": f"Found {len(all_results)} results for '{query}' across {len(cities)} cities",
            "results": all_results,
            "total_found": total_found,
            "query_tokens": list(combined_tokens),
            "wildcard_used": '*' in query
        }
    except Exception as e:
        logging.error(f"Error searching all cities for '{query}': {e}")
        return {
            "status": "error",
            "message": str(e),
            "results": []
        }
