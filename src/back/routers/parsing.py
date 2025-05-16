from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Form, Query
from typing import Dict, List, Optional
from celery.result import AsyncResult
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.core.parsers.tasks import (
    parse_city_task,
    parse_wikipedia_task,
    parse_google_places_task,
    parse_place_by_type_task,
    parse_web_scrape_task,
    update_place_description_task
)
from src.core.celery_app import app as celery_app
from src.configs.config import settings
from src.back.models.parsing_models import (
    TaskStatusResponse,
    UpdateDescriptionRequest
)

router = APIRouter(
    prefix="/parsing",
    tags=["parsing"],
    responses={404: {"description": "Not found"}},
)


@router.post("/parse-city")
async def parse_city(
    city: str = Form(..., description="City name to parse"),
    place_types: Optional[List[str]] = Query(None, description="Optional list of place types to parse")
):
    """
    Endpoint to parse both Wikipedia and Google Places data for a specific city
    
    Args:
        city: City name to parse
        place_types: Optional list of place types to parse. If not provided, all types will be parsed.
    """
    try:
        # Start the Celery task asynchronously
        task = parse_city_task.delay(city, place_types)
        return {"task_id": task.id, "status": "Task started", "message": f"Started parsing data for {city}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start parsing task: {str(e)}")


@router.post("/parse-wikipedia")
async def parse_wikipedia(
    city: str = Form(..., description="City name to parse Wikipedia data for")
):
    """
    Endpoint to parse only Wikipedia data for a specific city
    """
    try:
        task = parse_wikipedia_task.delay(city)
        return {"task_id": task.id, "status": "Task started", "message": f"Started parsing Wikipedia data for {city}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Wikipedia parsing task: {str(e)}")


@router.post("/parse-google-places")
async def parse_google_places(
    city: str = Form(..., description="City name to parse Google Places data for"),
    place_types: Optional[List[str]] = Query(None, description="Optional list of place types to parse")
):
    """
    Endpoint to parse Google Places data for specific or all place types in a city
    
    Args:
        city: City name to parse
        place_types: Optional list of place types to parse. If not provided, all types will be parsed.
    """
    try:
        task = parse_google_places_task.delay(city, place_types)
        
        # Create appropriate message based on place types
        place_types_msg = "all place types" if not place_types else f"place types: {', '.join(place_types)}"
        
        return {
            "task_id": task.id, 
            "status": "Task started", 
            "message": f"Started parsing Google Places data for {city} ({place_types_msg})"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Google Places parsing task: {str(e)}")


@router.post("/parse-place-by-type")
async def parse_place_by_type(
    city: str = Form(..., description="City name to parse"),
    place_type: str = Form(..., description="Place type to parse (e.g., restaurant, museum, etc.)")
):
    """
    Endpoint to parse places of a specific type in a city
    """
    try:
        task = parse_place_by_type_task.delay(city, place_type)
        return {
            "task_id": task.id, 
            "status": "Task started", 
            "message": f"Started parsing {place_type} in {city}"
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start parsing task: {str(e)}")


@router.post("/parse-website")
async def parse_website(
    url: str = Form(..., description="Website URL to parse")
):
    """
    Endpoint to parse information from a website URL
    """
    try:
        task = parse_web_scrape_task.delay(url)
        return {"task_id": task.id, "status": "Task started", "message": f"Started parsing website: {url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start website parsing task: {str(e)}")


@router.post("/update-place-description")
async def update_place_description(request: UpdateDescriptionRequest):
    """
    Endpoint to update a place description and generate embeddings
    """
    try:
        task = update_place_description_task.delay(request.description, request.place_data)
        return {
            "task_id": task.id, 
            "status": "Task started", 
            "message": "Started updating place description and generating embeddings"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update place description: {str(e)}")


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of a parsing task by its ID
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
        )
        
        # Include result if the task is completed
        if task_result.status == 'SUCCESS':
            response.result = task_result.result
        # Include error if the task failed
        elif task_result.status == 'FAILURE':
            response.error = str(task_result.result)
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}") 