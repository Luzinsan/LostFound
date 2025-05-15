from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.semantic_search.tasks import search_ball_tree_task, search_all_cities_ball_tree_task
from src.back.models.models import SearchResponse


router = APIRouter(
    prefix="/semantic",
    tags=["semantic_search"],
    responses={404: {"description": "Not found"}},
)

@router.get("/city/{city}", response_model=SearchResponse)
async def semantic_search_city(
    city: str,
    query: str,
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Semantic search for places in a specific city using ball tree.
    
    Features:
    * 🧠 Natural language query understanding
    * 🎯 Semantic similarity-based ranking
    * 📊 Detailed information for each result
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    
    Args:
        city: City to search in
        query: Natural language search query
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
            
        if city not in settings.CITIES:
            error_msg = f"City {city} not found. Available cities: {', '.join(settings.CITIES)}"
            logging.error(f"{error_msg} - Invalid city name provided")
            raise HTTPException(
                status_code=404,
                detail=error_msg
            )
        
        result = search_ball_tree_task.delay(city, query, limit, types)
        search_results = result.get()
        
        if search_results.get("status") != "success":
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

@router.get("/all", response_model=SearchResponse)
async def semantic_search_all_cities(
    query: str,
    cities: Optional[List[str]] = Query(None, description="Cities to search in. If not provided, searches in all cities"),
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Semantic search for places across all available cities using ball tree.
    
    Features:
    * 🌍 Parallel search across all specified cities
    * 🧠 Natural language query understanding
    * 🎯 Semantic similarity-based ranking
    * 🔄 Combined relevance scoring:
      - 70% weight for semantic similarity
      - 30% weight for place type matching
    * 📊 Detailed information for each result
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    
    Args:
        query: Natural language search query
        cities: List of cities to search in (if not provided, searches in all cities)
        types: List of place types to filter by (optional)
        limit: Maximum number of results (1-50)
        
    Returns:
        SearchResponse containing:
        * List of found places with detailed information
        * Relevance scores (combined and semantic)
        * Total number of results found across all cities
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
            
        if cities is None:
            cities = settings.CITIES
        
        # Validate cities
        invalid_cities = [city for city in cities if city not in settings.CITIES]
        if invalid_cities:
            error_msg = f"Invalid cities: {', '.join(invalid_cities)}. Available cities: {', '.join(settings.CITIES)}"
            logging.error(f"{error_msg} - Invalid city names provided")
            raise HTTPException(
                status_code=400,
                detail=error_msg
            )
        
        result = search_all_cities_ball_tree_task.delay(query, cities, limit, types)
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
        error_msg = "Internal server error during multi-city semantic search"
        logging.error(f"{error_msg} - Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        ) 