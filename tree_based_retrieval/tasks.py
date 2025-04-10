import logging
from celery import group
from config import settings
from utils.mongodb_handler import mongo_manager
from tree_based_retrieval.ball_tree import SimilaritySearchEngine
from typing import List, Dict, Any
from celery_app import app
from embeddings.BERT_ru import RussianBERTEmbedder
import numpy as np

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
        
        # Build ball tree and save to MongoDB
        try:
            search_engine = SimilaritySearchEngine(id_embedding_dict, city)
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
def build_all_cities_ball_trees_task() -> dict:
    """
    Task to build ball trees for all cities.
    """
    try:
        logging.info(f"[Task] Starting ball tree building for all cities: {settings.CITIES}")
        
        # Start tasks for each city
        task_group = group(build_city_ball_tree_task.s(city) for city in settings.CITIES)
        result = task_group.apply_async()
        results = result.join(disable_sync_subtasks=False)
        
        return {
            "status": "success",
            "message": f"Ball trees built for all cities: {settings.CITIES}",
            "results": len(results)
        }
    except Exception as e:
        logging.error(f"Error building ball trees for all cities: {e}")
        return {"status": "error", "message": str(e)}

@app.task
def search_ball_tree_task(city: str, query: str, limit: int = 10) -> dict:
    """
    Searches using the ball tree for the given query within a specific city.
    """
    try:
        logging.info(f"[Task] Searching for '{query}' in city: {city}")
        
        # Create search engine from MongoDB data
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
                doc_data = mongo_manager.load({"_id": doc_id}, "places")
                if doc_data:
                    doc_data = doc_data[0]
                    detailed_results.append({
                        "doc_id": doc_id,
                        "score": score,
                        "name": doc_data.get("displayName", {}),
                        "address": doc_data.get("shortFormattedAddress", "Unknown"),
                        "types": doc_data.get("types", []),
                        "summary": doc_data.get("editorialSummary", 'Unknown'),
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
def search_all_cities_ball_tree_task(query: str, cities: List[str] = None, limit: int = 10) -> dict:
    """
    Searches for the query across all specified cities using ball trees.
    """
    try:
        # Use all cities from settings if none specified
        if cities is None:
            cities = settings.CITIES
            
        logging.info(f"[Task] Searching for '{query}' across cities: {cities}")
        
        # Search in each city
        tasks = []
        for city in cities:
            tasks.append(search_ball_tree_task.s(city, query, limit))
            
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