import logging
from celery import group, chain
from typing import List, Dict, Any, Optional
import numpy as np
import time

import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.utils.mongodb_handler import mongo_manager
from src.core.celery_app import app
from src.core.semantic_search.BERT_ru import RussianBERTEmbedder
from src.core.semantic_search.ball_tree import SimilaritySearchEngine
from src.core.parsers import google_places


@app.task
def build_city_ball_tree_task(city: str) -> dict:
    """
    Task to build a ball tree for all locations in a specific city and store it in MongoDB.
    """
    try:
        logging.info(f"[Task] Starting ball tree building for city: {city}")
        
        # Get city information
        city_data = mongo_manager.load({"city": city}, "cities")
        if not city_data or len(city_data) == 0:
            logging.error(f"No city data found for: {city}")
            return {"status": "error", "message": f"No city data found for: {city}"}
        
        # Extract place IDs from city data
        place_ids = city_data[0].get('places', [])
        if not place_ids:
            logging.error(f"No place IDs found for city: {city}")
            return {"status": "error", "message": f"No place IDs found for city: {city}"}
        
        # Load location data and embeddings for each place ID
        id_embedding_dict = {}
        for place_id in place_ids:
            try:
                place_data = mongo_manager.load({"_id": place_id}, "places")
                if place_data and 'embedding' in place_data[0]:
                    id_embedding_dict[place_id] = np.array(place_data[0]['embedding'])
            except Exception as e:
                logging.error(f"Error loading place data for ID {place_id}: {e} - Failed to process individual place data")
                continue
        
        if not id_embedding_dict:
            logging.error(f"No embeddings found for city: {city}")
            return {"status": "error", "message": f"No embeddings found for city: {city}"}
        
      
        try:
            SimilaritySearchEngine(id_embedding_dict, city)
        except Exception as e:
            error_msg = f"Failed to build ball tree for city: {city}"
            logging.error(f"{error_msg} - Error during ball tree construction: {e}")
            return {"status": "error", "message": error_msg}
        
        return {
            "status": "success",
            "message": f"Ball tree built for city: {city}",
            "num_items": len(id_embedding_dict)
        }
    except Exception as e:
        logging.error(f"Error building ball tree for city {city}: {e}")
        return {"status": "error", "message": str(e)}

@app.task
def build_all_cities_ball_trees_task(cities: Optional[List[str]] = None) -> dict:
    """
    Task to build ball trees for specified cities or all cities if none specified.
    
    Args:
        cities: Optional list of city names. If None, processes all cities from settings.
    
    Returns:
        Dictionary with status and results from each city's ball tree building task
    """
    try:
        cities_to_process = cities if cities else settings.CITIES
        
        logging.info(f"[Task] Starting ball tree building for cities: {cities_to_process}")
        
        # Start tasks for each city
        task_group = group(build_city_ball_tree_task.s(city) for city in cities_to_process)
        result = task_group.apply_async()
        results = result.join(disable_sync_subtasks=False)
        
        return {
            "status": "success",
            "message": f"Ball trees built for cities: {cities_to_process}",
            "cities_processed": cities_to_process,
            "results": results
        }
    except Exception as e:
        logging.error(f"Error building ball trees for cities {cities_to_process}: {e}")
        return {"status": "error", "message": str(e)}

@app.task
def search_ball_tree_task(city: str, query: str, limit: int = 10, types: Optional[List[str]] = None) -> dict:
    """
    Searches using the ball tree for the given query within a specific city.
    
    Args:
        city: The city to search in
        query: The natural language search query
        limit: Maximum number of results to return
        types: Optional list of place types to filter by
    """
    try:
        logging.info(f"[Task] Searching for '{query}' in city: {city} with types: {types} and limit: {limit}")
        
        try:
            search_engine = SimilaritySearchEngine.from_mongodb(city)
            if search_engine is None:
                error_msg = f"No ball tree found for city: {city}"
                logging.error(f"{error_msg} - Ball tree data is missing in the database")
                return {
                    "status": "error", 
                    "message": error_msg,
                    "results": []
                }
        except Exception as e:
            error_msg = f"Failed to load ball tree for city: {city}"
            logging.error(f"{error_msg} - Error during ball tree loading: {e}")
            return {
                "status": "error",
                "message": error_msg,
                "results": []
            }
        
        # Generate query embedding
        try:
            query_embedding = RussianBERTEmbedder().text_to_embedding(query)
        except Exception as e:
            error_msg = f"Failed to generate embedding for query: {query}"
            logging.error(f"{error_msg} - Error during query embedding generation: {e}")
            return {
                "status": "error",
                "message": error_msg,
                "results": []
            }
        
        # Perform search
        try:
            results = search_engine.find_similar(query_embedding, top_k=limit)
        except Exception as e:
            error_msg = f"Failed to perform similarity search for query: {query}"
            logging.error(f"{error_msg} - Error during ball tree search: {e}")
            return {
                "status": "error",
                "message": error_msg,
                "results": []
            }
        
        # Get additional document details from MongoDB
        detailed_results = []
        for doc_id, score in results.items():
            try:
                # Базовый фильтр для документа
                mongo_filter = {"_id": doc_id}
                
                # Добавляем фильтр по типам, если указан
                if types and len(types) > 0:
                    mongo_filter["types"] = {"$in": types}
                
                doc_data = mongo_manager.load(mongo_filter, "places")
                if doc_data:
                    doc_data = doc_data[0]
                    detailed_results.append({
                        "doc_id": doc_id,
                        "score": score,
                        "name": doc_data.get("displayName", {}),
                        "address": doc_data.get("shortFormattedAddress", "Unknown"),
                        "types": doc_data.get("types", []),
                        "summary": doc_data.get("editorialSummary", 'Unknown'),
                        "photos": doc_data.get("photos", None),
                        "city": city 
                    })
            except Exception as e:
                logging.error(f"Error loading details for document {doc_id}: {e} - Failed to process individual search result")
                continue
        
        return {
            "status": "success",
            "message": f"Found {len(detailed_results)} results for '{query}' in {city}",
            "results": detailed_results,
            "total_found": len(detailed_results)
        }
        
    except Exception as e:
        error_msg = f"Error searching ball tree for '{query}' in {city}"
        logging.error(f"{error_msg} - Unexpected error during search operation: {e}")
        return {
            "status": "error", 
            "message": error_msg,
            "results": []
        }

@app.task
def search_all_cities_ball_tree_task(query: str, cities: List[str] = None, limit: int = 10, types: Optional[List[str]] = None) -> dict:
    """
    Searches for the query across all specified cities using ball trees.
    
    Args:
        query: The natural language search query
        cities: List of cities to search in (if None, all cities in settings.CITIES are used)
        limit: Maximum number of results to return per city
        types: Optional list of place types to filter by
    """
    try:
        cities = cities if cities else settings.CITIES
            
        logging.info(f"[Task] Searching for '{query}' across cities: {cities}")
        
        # Search in each city
        tasks = []
        for city in cities:
            tasks.append(search_ball_tree_task.s(city, query, limit, types))
            
        # Execute all search tasks in parallel
        task_group = group(tasks)
        result = task_group.apply_async()
        city_results = result.join(disable_sync_subtasks=False)
        
        # Combine and aggregate results
        all_results = []
        total_found = 0
        
        for city_result in city_results:
            if city_result.get("status") == "success":
                all_results.extend(city_result.get("results", []))
                total_found += city_result.get("total_found", 0)
                
        # Sort combined results by score
        all_results = sorted(all_results, key=lambda x: x.get("score", 0), reverse=True)[:limit]
        
        return {
            "status": "success",
            "message": f"Found {len(all_results)} results for '{query}' across {len(cities)} cities",
            "results": all_results,
            "total_found": total_found
        }
    except Exception as e:
        logging.error(f"Error searching all cities for '{query}': {e}")
        return {
            "status": "error",
            "message": str(e),
            "results": []
        }

@app.task
def create_embeddings_for_cities(cities: Optional[List[str]] = None) -> Dict:
    """
    Task to create embeddings for all places in specified cities or all cities if none specified.
    Spawns parallel tasks for creating embeddings, both at the city level and place level.
    
    Args:
        cities: Optional list of city names. If None, processes all cities from settings.
                
    Returns:
        Dictionary with statistics about the embedding creation process
    """
    cities_to_process = cities if cities else settings.CITIES
    
    logging.info(f"Starting batch embedding creation for cities: {cities_to_process}")
    
    task_group = group(create_embeddings_for_city.s(city) for city in cities_to_process)
    result = task_group.apply_async()
    
    return {
        "status": "success",
        "message": f"Started parallel embedding creation tasks for {len(cities_to_process)} cities: {', '.join(cities_to_process)}",
        "city_tasks_id": result.id
    }


@app.task
def create_embeddings_for_city(city: str) -> Dict:
    """
    Task to create embeddings for all places in a specific city.
    Runs as a subtask of create_embeddings_for_cities.
    
    Args:
        city: City name to process
                
    Returns:
        Dictionary with statistics about the embedding creation process for this city
    """
    try:
        query = {"city": city}
        places = mongo_manager.load(query, "places")
        
        if not places:
            logging.info(f"No places found for city: {city}")
            return {
                "status": "success",
                "city": city,
                "places_count": 0,
                "message": "No places found"
            }
            
        places_count = len(places)
        logging.info(f"Starting parallel tasks for {places_count} places in {city}")
        
        tasks = group(create_location_embeddings.s(place) for place in places)
        result = tasks.apply_async()
        
        logging.info(f"Started {places_count} parallel embedding tasks for {city}")
        
        return {
            "status": "success",
            "city": city,
            "places_count": places_count,
            "task_id": result.id
        }
        
    except Exception as e:
        error_msg = f"Error processing city {city}: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "city": city,
            "message": error_msg
        }

@app.task
def create_location_embeddings(location_data: dict) -> Dict:
    """
    Creates embeddings for a location using the collected data.
    
    Args:
        location_data: Dictionary containing location information including:
             
    Returns:
        Dictionary with the original data plus the embedding
    """
    try:    
        embedder = RussianBERTEmbedder()
        location_data['embedding'] = embedder.text_to_embedding(location_data['search_text'] \
                                                                + ' ' + location_data.get('reviews_flattened', '')).tolist()
        location_data['timestamp_embedding'] = time.time()
        mongo_manager.save(location_data, "places")
        return location_data
        
    except Exception as e:
        logging.error(f"Error creating embeddings for location {location_data.get('name', 'Unknown')}: {e}")
        return location_data 

@app.task
def build_embeddings_and_ball_trees_task(cities: Optional[List[str]] = None) -> dict:
    """
    Task to create embeddings and build ball trees for specified cities or all cities if none specified.
    
    Args:
        cities: Optional list of city names. If None, processes all cities from settings.
    
    Returns:
        Dictionary with status and started task information
    """
    try:
        cities_to_process = cities if cities else settings.CITIES
        
        logging.info(f"[Task] Starting combined embeddings creation and ball tree building for cities: {cities_to_process}")
        chain_result = chain(
            create_embeddings_for_cities.s(cities_to_process),
            build_all_cities_ball_trees_task.si(cities_to_process)
        ).apply_async()
        
        return {
            "status": "success",
            "message": f"Tasks started for creating embeddings and building ball trees for cities: {cities_to_process}",
            "cities_initiated": cities_to_process,
            "chain_task_id": chain_result.id
        }
    except Exception as e:
        logging.error(f"Error starting embeddings and ball trees tasks for cities {cities_to_process}: {e}")
        return {"status": "error", "message": str(e)} 