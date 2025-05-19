from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.indexing_search.tasks import search_index_task, search_all_cities_task, build_all_indices_task
from src.back.models.models import SearchResponse


router = APIRouter(
    prefix="/index_search",
    tags=["index_search"],
    responses={404: {"description": "Not found"}},
)

@router.post("/create-indexes")
async def create_indexes(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to create indexes for. If not provided, creates indexes for all cities.")
):
    """
    Create or update search indexes for the specified cities.
    
    This endpoint builds inverted indexes for all places in the specified cities.
    These indexes are used for full-text search with TF-IDF ranking.
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Status message indicating the result of the operation
    """
    try:
        result = build_all_indices_task.delay(cities)
        index_results = result.get()
        
        if index_results.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=index_results.get("message", "Index creation failed")
            )
        
        # Format response message
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Search indexes created successfully for {cities_msg}",
            "cities_processed": index_results.get("cities_processed", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create indexes: {str(e)}"
        )

@router.get("/search", response_model=SearchResponse)
async def search(
    query: str,
    cities: Optional[List[str]] = Query(None, description="Cities to search in. If not provided, searches in all cities. Can be a single city or multiple cities."),
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(50, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Search for places using inverted index.
    
    Features:
    * 🔍 Keyword-based search support
    * 🎯 TF-IDF based ranking
    * 🔄 Wildcard search support (e.g., "rest*" for restaurants)
    * 📊 Automatic query correction
    * 🏷️ Filter by place types (museum, restaurant, etc.)
    * 🌍 Search in one specific city, multiple cities, or all cities
    
    Args:
        query: Search query (supports wildcard characters)
        cities: List of cities to search in. If not provided, searches in all available cities
        types: List of place types to filter by (optional)
        limit: Maximum number of results (1-50)
        
    Returns:
        SearchResponse containing:
        * List of found places with detailed information
        * Total number of results found
        * Query tokens used
        * Wildcard search usage information
    """
    try:
        cities = cities if cities else settings.CITIES
        
        if len(cities) == 1:
            result = search_index_task.delay(cities[0], query, limit, types)
        else:
            result = search_all_cities_task.delay(query, cities, limit, types)
        
        search_results = result.get()
        
        if search_results.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=search_results.get("message", "Search failed")
            )
        
        return search_results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during search: {str(e)}"
        ) 