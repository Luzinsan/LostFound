from fastapi import APIRouter, HTTPException
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.indexing_search.tasks import build_all_indices_task
from src.back.models.models import SystemStatus

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

@router.get("/cities")
async def get_cities():
    """
    Get the list of available cities.
    
    Returns:
        List of cities available for search
    """
    return {"cities": settings.CITIES}

@router.get("/place-types")
async def get_place_types():
    """
    Get the list of available place types.
    
    Returns:
        List of place types available in the system
    """
    return {"place_types": settings.PLACE_TYPES} 