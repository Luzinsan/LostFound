from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from config import settings
from indexing.tasks import search_index_task, search_all_cities_task
from models import SearchResponse

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

@router.get("/city/{city}", response_model=SearchResponse)
async def search_city(
    city: str,
    query: str,
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Search for places in a specific city.
    
    Args:
        city: City to search in
        query: Search query
        limit: Maximum number of results to return (1-50)
        
    Returns:
        SearchResponse containing the search results
    """
    if city not in settings.CITIES:
        raise HTTPException(
            status_code=404,
            detail=f"City {city} not found. Available cities: {', '.join(settings.CITIES)}"
        )
    
    result = search_index_task.delay(city, query, limit)
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
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
) -> SearchResponse:
    """
    Search for places across multiple cities.
    
    Args:
        query: Search query
        cities: List of cities to search in (optional)
        limit: Maximum number of results to return (1-50)
        
    Returns:
        SearchResponse containing the search results
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
    
    result = search_all_cities_task.delay(query, cities, limit)
    search_results = result.get()
    
    if search_results.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=search_results.get("message", "Search failed")
        )
    
    return search_results 