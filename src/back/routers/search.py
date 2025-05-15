from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.indexing_search.tasks import search_index_task, search_all_cities_task
from src.back.models.models import SearchResponse


router = APIRouter(
    prefix="/index_search",
    tags=["index_search"],
    responses={404: {"description": "Not found"}},
)

@router.get("/city/{city}", response_model=SearchResponse)
async def search_city(
    city: str,
    query: str,
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Search for places in a specific city using inverted index.
    
    Features:
    * 🔍 Keyword-based search support
    * 🎯 TF-IDF based ranking
    * 🔄 Wildcard search support (e.g., "rest*" for restaurants)
    * 📊 Automatic query correction
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    
    Args:
        city: City to search in
        query: Search query (supports wildcard characters)
        types: List of place types to filter by (optional)
        limit: Maximum number of results (1-50)
        
    Returns:
        SearchResponse containing:
        * List of found places with detailed information
        * Total number of results found
        * Query tokens used
        * Wildcard search usage information
    """
    if city not in settings.CITIES:
        raise HTTPException(
            status_code=404,
            detail=f"City {city} not found. Available cities: {', '.join(settings.CITIES)}"
        )
    
    result = search_index_task.delay(city, query, limit, types)
    search_results = result.get()
    
    if search_results.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=search_results.get("message", "Search failed")
        )
    
    return search_results

@router.get("/all", response_model=SearchResponse)
async def search_all_cities(
    query: str,
    cities: Optional[List[str]] = Query(None, description="Cities to search in. If not provided, searches in all cities"),
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Search for places across all available cities using inverted index.
    
    Features:
    * 🌍 Parallel search across all specified cities
    * 🔍 Keyword-based search support
    * 🎯 TF-IDF based ranking
    * 🔄 Wildcard search support
    * 📊 Automatic query correction
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    
    Args:
        query: Search query (supports wildcard characters)
        cities: List of cities to search in (if not provided, searches in all cities)
        types: List of place types to filter by (optional)
        limit: Maximum number of results (1-50)
        
    Returns:
        SearchResponse containing:
        * List of found places with detailed information
        * Total number of results found across all cities
        * Query tokens used
        * Wildcard search usage information
    """
    if cities is None:
        cities = settings.CITIES
    
    # Validate cities
    invalid_cities = [city for city in cities if city not in settings.CITIES]
    if invalid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cities: {', '.join(invalid_cities)}. Available cities: {', '.join(settings.CITIES)}"
        )
    
    result = search_all_cities_task.delay(query, cities, limit, types)
    search_results = result.get()
    
    if search_results.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=search_results.get("message", "Search failed")
        )
    
    return search_results 