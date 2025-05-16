from fastapi import APIRouter, Query
import sys, os
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.back.models.models import SystemStatus, CityInfo, WikipediaInfo, CitiesResponse
from src.utils.mongodb_handler import mongo_manager

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

@router.get("/status", response_model=SystemStatus)
async def system_status() -> SystemStatus:
    """
    Get the current system status.
    
    Returns:
        SystemStatus containing information about the system state
    """
    return {
        "status": "operational",
        "cities": settings.CITIES,
        "place_types": settings.PLACE_TYPES
    }


@router.get("/cities", response_model=CitiesResponse)
async def get_cities(
        cities: Optional[List[str]] = Query(None, description="Available cities in system. If not provided, returns all cities.")
    ) -> CitiesResponse:
    """
    Get the list of available cities with detailed information from Wikipedia.
    
    Args:
        cities: Optional list of city names to filter results for specific cities
    
    Returns:
        CitiesResponse containing detailed information about cities
    """
    cities_with_info: List[CityInfo] = []
    
    cities_to_process = cities if cities else settings.CITIES
    
    for city_name in cities_to_process:
        city_data_list = mongo_manager.load({"city": city_name}, "cities")
        
        if city_data_list and len(city_data_list) > 0 and "wikipedia" in city_data_list[0]:
            city_data = city_data_list[0]
            
            wiki_info = WikipediaInfo(
                url=city_data["wikipedia"]["url"],
                title=city_data["wikipedia"]["title"],
                summary=city_data["wikipedia"]["summary"]
            )
            
            city_info = CityInfo(city=city_name, wikipedia=wiki_info)
        else:
            city_info = CityInfo(city=city_name, wikipedia=None)
            
        cities_with_info.append(city_info)
    
    response = CitiesResponse(cities=cities_with_info)
    return response


@router.get("/place-types")
async def get_place_types():
    """
    Get the list of available place types.
    
    Returns:
        List of place types available in the system
    """
    return {"place_types": settings.PLACE_TYPES} 