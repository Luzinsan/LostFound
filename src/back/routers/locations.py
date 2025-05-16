from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import sys, os
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.back.models.models import (
    LocationListResponse,
    PaginationParams,
    LocationFilters,
    BasePlace,
    DetailedPlace
)
from src.utils.mongodb_handler import mongo_manager


router = APIRouter(
    prefix="/locations",
    tags=["locations"],
    responses={404: {"description": "Not found"}},
)

async def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(10, ge=1, le=100, description="Number of items per page")
) -> PaginationParams:
    """Dependency for pagination parameters."""
    return PaginationParams(page=page, per_page=per_page)

async def get_location_filters(
    city: Optional[str] = Query(None, description="Filter by city"),
    types: Optional[List[str]] = Query(None, description="Filter by place types", example=["cafe", "restaurant"]),
) -> LocationFilters:
    """Dependency for location filters."""
    return LocationFilters(
        city=city,
        types=types
    )

@router.get("", response_model=LocationListResponse)
async def list_locations(
    pagination: PaginationParams = Depends(get_pagination_params),
    filters: LocationFilters = Depends(get_location_filters)
) -> LocationListResponse:
    """
    Get a paginated list of locations with optional filtering.
    
    Args:
        pagination: Pagination parameters
        filters: Filtering criteria
        
    Returns:
        Paginated list of locations matching the criteria
    """
    try:
        query = {}
        if filters.city:
            query["city"] = filters.city
        if filters.types:
            query["types"] = {"$in": filters.types}
        
        skip = (pagination.page - 1) * pagination.per_page
        paginated_data = mongo_manager.load_paginated(
            query=query,
            collection_name="places",
            skip=skip,
            limit=pagination.per_page
        )
        
        results = []
        for loc in paginated_data["results"]:
            result = BasePlace(
                doc_id=loc["_id"],
                name=loc.get("displayName", ""),
                city=loc.get("city", ""),
                types=loc.get("types", []),
                address=loc.get("shortFormattedAddress"),
                summary=loc.get("editorialSummary"),
                photos=loc.get("photos", None)
            )
            results.append(result)
        
        return LocationListResponse(
            status="success",
            results=results,
            pagination={
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": (paginated_data["total"] + pagination.per_page - 1) // pagination.per_page
            },
            filters=filters.dict(exclude_none=True),
            total=paginated_data["total"]
        )
        
    except Exception as e:
        logging.error(f"Error fetching locations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{location_id}", response_model=DetailedPlace)
async def get_location_details(
    location_id: str
) -> DetailedPlace:
    """
    Get detailed information about a specific location.
    
    Args:
        location_id: Unique identifier of the location
        
    Returns:
        Detailed information about the location
    """
    try:
        # Get location details
        location_data = mongo_manager.load({"_id": location_id}, "places")
        if not location_data:
            raise HTTPException(
                status_code=404,
                detail=f"Location with ID {location_id} not found"
            )
        
        location = location_data[0]
        
        reviews = [
            dict(author_name=review.get("authorAttribution", {}).get("displayName", ""),
                rating=review.pop("rating"),
                text=review.pop("text", {}).get("text", ""),
                time=review.pop("publishTime"),
                relative_time_description=review.pop("relativePublishTimeDescription"),
                profile_photo_url=review.get("authorAttribution", {}).get("photoUri", "")
        ) for review in location.get("reviews", [])]
            
            
        result = DetailedPlace(
            doc_id=location["_id"],
            name=location.get("displayName", ""),
            city=location.get("city", ""),
            types=location.get("types", []),
            address=location.get("shortFormattedAddress"),
            summary=location.get("editorialSummary"),
            rating=location.get("rating"),
            user_ratings_total=location.get("userRatingCount"),
            price_level=location.get("priceLevel"),
            reviews=reviews,
            googleMapsUri=location.get("googleMapsUri", None),
            photos=location.get("photos", None)
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Error fetching location details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 