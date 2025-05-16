from pydantic import BaseModel, Field, conint
from typing import List, Optional, Dict, Any, Annotated



class BasePlace(BaseModel):
    """Base model representing a place with essential information from parsing."""
    doc_id: str = Field(..., description="Unique identifier of the place")
    name: str = Field(..., description="Name of the place")
    city: str = Field(..., description="City where the place is located")
    types: List[str] = Field(..., description="List of place types")
    address: Optional[str] = Field(None, description="Address of the place")
    summary: Optional[str] = Field(None, description="Description or summary of the place")
    photos: Optional[List[str]] = Field(None, description="List of photo URLs for the place")

class Review(BaseModel):
    """Model representing a review for a place."""
    author_name: str = Field(..., description="Name of the review author")
    rating: int = Field(..., description="Rating given by the author (1-5)")
    text: str = Field(..., description="Review text content")
    time: Optional[str] = Field(None, description="Timestamp of the review")
    relative_time_description: Optional[str] = Field(None, description="Relative time description (e.g., '2 months ago')")
    profile_photo_url: Optional[str] = Field(None, description="URL of the author's profile photo")

class SearchedPlace(BasePlace):
    """Model representing a place with search-specific information."""
    score: float = Field(..., description="Search relevance score")

class DetailedPlace(BasePlace):
    """Model representing a place with detailed information."""
    rating: Optional[float] = Field(None, description="Average rating of the place")
    user_ratings_total: Optional[int] = Field(None, description="Total number of user ratings")
    price_level: Optional[str] = Field(None, description="Price level (0-4)")
    reviews: Optional[List[Review]] = Field(None, description="List of reviews")
    googleMapsUri: Optional[str] = Field(None, description="Google Maps URL of the place")

class SearchResponse(BaseModel):
    """Model representing the response from a search operation."""
    status: str = Field(..., description="Status of the search operation")
    results: List[SearchedPlace] = Field(..., description="List of search results")
    total_found: Optional[int] = Field(..., description="Total number of matches found")
    query_tokens: Optional[List[str]] = Field(None, description="Tokens used in the search query")
    wildcard_used: Optional[bool] = Field(None, description="Whether wildcard search was used")
    message: Optional[str] = Field(None, description="Additional message about the search")

class PaginationParams(BaseModel):
    """Model for pagination parameters."""
    page: Annotated[int, Field(ge=1)] = Field(1, description="Page number (1-based)")
    per_page: Annotated[int, Field(ge=1, le=100)] = Field(10, description="Number of items per page")

class LocationFilters(BaseModel):
    """Model for location filtering parameters."""
    city: Optional[str] = Field(None, description="Filter by city")
    types: Optional[List[str]] = Field(None, description="Filter by place types")

class LocationListResponse(BaseModel):
    """Model for paginated location list response."""
    status: str = Field(..., description="Status of the operation")
    results: List[BasePlace] = Field(..., description="List of locations")
    pagination: Dict[str, int] = Field(..., description="Pagination information")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters")
    total: int = Field(..., description="Total number of locations matching filters")

class WikipediaInfo(BaseModel):
    """Model representing information from Wikipedia."""
    url: str = Field(..., description="URL of the Wikipedia page")
    title: str = Field(..., description="Title of the Wikipedia article")
    summary: str = Field(..., description="Summary of the Wikipedia article")

class CityInfo(BaseModel):
    """Model representing detailed information about a city."""
    city: str = Field(..., description="Name of the city")
    wikipedia: Optional[WikipediaInfo] = Field(None, description="Information from Wikipedia about the city")

class SystemStatus(BaseModel):
    """Model representing the system status."""
    status: str = Field(..., description="Current system status")
    cities: List[str] = Field(..., description="List of available cities")
    place_types: List[str] = Field(..., description="List of available place types")

class CitiesResponse(BaseModel):
    """Model representing detailed information about cities."""
    cities: List[CityInfo] = Field(..., description="List of cities with detailed information")

class ErrorResponse(BaseModel):
    """Model representing an error response."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code") 