from fastapi import APIRouter, HTTPException
import sys, os
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.indexing_search.tasks import build_all_indices_task
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

@router.post("/index/rebuild")
async def rebuild_index():
    """
    Rebuild the search index.
    
    Returns:
        Status message indicating the result of the operation
    """
    try:
        result = build_all_indices_task.delay()
        index_results = result.get()
        
        if index_results.get("status") != "success":
            raise HTTPException(
                status_code=500,
                detail=index_results.get("message", "Index rebuild failed")
            )
        
        return {
            "status": "success",
            "message": "Index rebuild completed successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/cities", response_model=CitiesResponse)
async def get_cities(city: Optional[str] = None) -> CitiesResponse:
    """
    Get the list of available cities with detailed information from Wikipedia.
    
    Args:
        city: Optional city name to filter results for a specific city
    
    Returns:
        CitiesResponse containing detailed information about all cities or a specific city
    """
    # Получаем информацию о городах из MongoDB
    cities_with_info: List[CityInfo] = []
    
    # Filter cities if a specific city is requested
    cities_to_process = [city] if city and city in settings.CITIES else settings.CITIES
    
    for city_name in cities_to_process:
        # Ищем информацию о городе в базе данных
        city_data_list = mongo_manager.load({"city": city_name}, "cities")
        
        if city_data_list and len(city_data_list) > 0 and "wikipedia" in city_data_list[0]:
            # Если информация о городе найдена, добавляем ее в формате CityInfo
            city_data = city_data_list[0]  # Берем первый элемент из списка результатов
            
            # Создаем объект WikipediaInfo с информацией из Wikipedia
            wiki_info = WikipediaInfo(
                url=city_data["wikipedia"]["url"],
                title=city_data["wikipedia"]["title"],
                summary=city_data["wikipedia"]["summary"]
            )
            
            # Создаем объект CityInfo с информацией о городе
            city_info = CityInfo(city=city_name, wikipedia=wiki_info)
        else:
            # Если информации нет, добавляем только название города
            city_info = CityInfo(city=city_name, wikipedia=None)
            
        cities_with_info.append(city_info)
    
    # Создаем и возвращаем объект CitiesResponse
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