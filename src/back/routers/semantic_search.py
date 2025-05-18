from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Optional, Dict
import logging
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.semantic_search.tasks import (
    search_ball_tree_task, 
    search_all_cities_ball_tree_task,
    create_embeddings_for_cities,
    build_all_cities_ball_trees_task,
    build_embeddings_and_ball_trees_task
)
from src.back.models.models import SearchResponse


router = APIRouter(
    prefix="/semantic",
    tags=["semantic_search"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    query: str,
    cities: Optional[List[str]] = Query(None, description="Cities to search in. If not provided, searches in all cities. Can be a single city or multiple cities."),
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Semantic search for places using ball tree.
    
    Features:
    * 🧠 Natural language query understanding
    * 🎯 Semantic similarity-based ranking
    * 🔄 Combined relevance scoring:
      - 70% weight for semantic similarity
      - 30% weight for place type matching
    * 📊 Detailed information for each result
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    * 🌍 Search in one specific city, multiple cities, or all cities
    
    Args:
        query: Natural language search query
        cities: List of cities to search in. If not provided, searches in all available cities
        types: List of place types to filter by (optional)
        limit: Maximum number of results (1-50)
        
    Returns:
        SearchResponse containing:
        * List of found places with detailed information
        * Relevance scores (combined and semantic)
        * Total number of results found
        * Query tokens used
    """
    try:
        if not query.strip():
            error_msg = "Search query cannot be empty"
            logging.error(f"{error_msg} - Empty query provided")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        cities = cities if cities else settings.CITIES
        result = (
            search_ball_tree_task.delay(cities[0], query, limit, types) 
            if len(cities) == 1 
            else search_all_cities_ball_tree_task.delay(query, cities, limit, types)
        )
        search_results = result.get()
        
        if search_results.get("status") not in ["success", "partial_success"]:
            error_msg = search_results.get("message", "Semantic search failed")
            logging.error(f"{error_msg} - Search task returned error status")
            raise HTTPException(
                status_code=500,
                detail=error_msg
            )
        return search_results
    except HTTPException:
        raise
    except Exception as e:
        error_msg = "Internal server error during semantic search"
        logging.error(f"{error_msg} - Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/create-ball-trees")
async def create_ball_trees(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to create ball trees for. If not provided, creates ball trees for all cities.")
) -> Dict:
    """
    Create or update ball trees for semantic search in the specified cities.
    
    This endpoint starts a background task that builds ball trees for all places in the specified cities.
    These ball trees are used for efficient semantic similarity search.
    
    Note: Before creating ball trees, you need to make sure that embeddings 
    have been created for all places using the /create-embeddings endpoint.
    
    The task runs asynchronously and the endpoint returns immediately with the task ID.
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Status message and task ID
    """
    try:
        task = build_all_cities_ball_trees_task.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started ball trees creation for {cities_msg}",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ball trees creation: {str(e)}"
        )

@router.post("/create-embeddings")
async def create_embeddings(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to create embeddings for. If not provided, creates embeddings for all cities.")
) -> Dict:
    """
    Create or update embeddings for all places in the specified cities.
    
    This endpoint starts a background task that processes places in the specified cities
    and creates semantic embeddings for them. These embeddings are used by the semantic search.
    
    The process runs asynchronously and may take some time to complete for large datasets.
    
    Note: After creating embeddings, you'll need to build ball trees using the /create-ball-trees
    endpoint to enable semantic search functionality.
    
    Features:
    * 🧠 Creates BERT embeddings for semantic search
    * 🚀 Processes places in parallel for better performance
    * 🌍 Can target specific cities or all available cities
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Dictionary containing:
        * Statistics about the started tasks
        * Task IDs for monitoring
        * Total number of places being processed
    """
    try:
        task = create_embeddings_for_cities.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started embedding creation for {cities_msg}",
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = "Failed to start embedding creation task"
        logging.error(f"{error_msg}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"{error_msg}: {str(e)}"
        )

@router.post("/create-search-data")
async def create_search_data(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to process. If not provided, processes all cities.")
) -> Dict:
    """
    Create or update all semantic search data (embeddings and ball trees) for specified cities.
    
    This endpoint starts background tasks that create embeddings and build ball trees
    for efficient semantic similarity search.
    
    This is a one-stop solution that replaces the need to call /create-embeddings
    and /create-ball-trees separately.
    
    The tasks run asynchronously and the endpoint returns immediately with the task ID.
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Status message and task ID
    """
    try:
        task = build_embeddings_and_ball_trees_task.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started semantic search data creation for {cities_msg}",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start semantic search data creation: {str(e)}"
        )