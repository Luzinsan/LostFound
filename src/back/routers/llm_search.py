from fastapi import APIRouter, HTTPException, Query, Form
from typing import List, Optional, Dict
import logging
import sys
import os
from pathlib import Path
from openai import OpenAI
from src.configs.config import settings  

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.core.semantic_search.tasks import (
    search_ball_tree_task, 
    search_all_cities_ball_tree_task,
    create_embeddings_for_cities,
    build_all_cities_ball_trees_task,
    build_embeddings_and_ball_trees_task
)
from src.back.models.models import SearchResponse


client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key= settings.GPT4_API_KEY,
)

router = APIRouter(
    prefix="/LLM",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

GPT_MODEL = "gpt-4o"
QUERY_REPHRASE_PROMPT = """Переформулируй поисковый запрос для улучшения релевантности результатов. 
Сохрани оригинальный смысл, но сделай его более подходящим для семантического поиска. 

Оригинальный запрос: {query}
Переформулированный запрос:"""

RESULT_SUMMARY_PROMPT = """Проанализируй топ-{limit} результатов поиска и сформулируй краткий ответ. 
Включи основные особенности и темы, используя информацию из этих результатов. 

Результаты поиска:
{results}

Краткий ответ:"""

def gpt_query(query: str) -> str:
    try:
        response = client.chat.completions.create(  # Изменен вызов API
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a search query optimization assistant"},
                {"role": "user", "content": QUERY_REPHRASE_PROMPT.format(query=query)}
            ],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT-4o query error: {str(e)}")
        return query 
    
def gpt_summary(results: List[Dict], limit: int) -> str:
    try:
        results_str = "\n".join([
            f"{i+1}. {res.get('name', '')} - {res.get('summary', '')[:200]}..."
            for i, res in enumerate(results[:limit])
        ])
        
        response = client.chat.completions.create(  # Изменен вызов API
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a search results summarizer"},
                {"role": "user", "content": RESULT_SUMMARY_PROMPT.format(limit=limit, results=results_str)}
            ],
            temperature=0.5,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT-4o summary error: {str(e)}")
        return "Не удалось сгенерировать суммаризацию результатов"


@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    query: str,
    cities: Optional[List[str]] = Query(None, description="Cities to search in."),
    types: Optional[List[str]] = Query(None, description="Place types to filter by"),
    limit: int = Query(10, ge=1, le=50)
) -> SearchResponse:
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
      
        optimized_query = gpt_query(query)
        logging.info(f"Optimized query: {optimized_query} (Original: {query})")
        
        cities = cities or settings.CITIES
        
        if len(cities) == 1:
            result = search_ball_tree_task.delay(cities[0], optimized_query, limit, types)
        else:
            result = search_all_cities_ball_tree_task.delay(optimized_query, cities, limit, types)
        
        search_results = result.get()
        
        if search_results.get("status") not in ["success", "partial_success"]:
            raise HTTPException(status_code=500, detail=search_results.get("message", "Search failed"))
        
        
        if search_results["results"]:
            summary = gpt_summary(search_results["results"], limit)
            search_results["gpt_summary"] = summary
        
        return SearchResponse(**search_results)
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/create-ball-trees")
async def create_ball_trees(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to create ball trees for. If not provided, creates ball trees for all cities.")
) -> Dict:
    """
    Create or update ball trees for semantic search in the specified cities.
    
    This endpoint starts a background task that builds ball trees for all places in the specified cities.
    These ball trees are used for efficient semantic similarity search.
    
    Note: Before creating ball trees, you need to make sure that embeddings 
    have been created for all places using the /create-embeddings endpoint.
    
    The task runs asynchronously and the endpoint returns immediately with the task ID.
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Status message and task ID
    """
    try:
        task = build_all_cities_ball_trees_task.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started ball trees creation for {cities_msg}",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ball trees creation: {str(e)}"
        )

@router.post("/create-embeddings")
async def create_embeddings(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to create embeddings for. If not provided, creates embeddings for all cities.")
) -> Dict:
    """
    Create or update embeddings for all places in the specified cities.
    
    This endpoint starts a background task that processes places in the specified cities
    and creates semantic embeddings for them. These embeddings are used by the semantic search.
    
    The process runs asynchronously and may take some time to complete for large datasets.
    
    Note: After creating embeddings, you'll need to build ball trees using the /create-ball-trees
    endpoint to enable semantic search functionality.
    
    Features:
    * 🧠 Creates BERT embeddings for semantic search
    * 🚀 Processes places in parallel for better performance
    * 🌍 Can target specific cities or all available cities
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Dictionary containing:
        * Statistics about the started tasks
        * Task IDs for monitoring
        * Total number of places being processed
    """
    try:
        task = create_embeddings_for_cities.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started embedding creation for {cities_msg}",
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = "Failed to start embedding creation task"
        logging.error(f"{error_msg}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"{error_msg}: {str(e)}"
        )

@router.post("/create-search-data")
async def create_search_data(
    cities: Optional[List[str]] = Query(None, description="Optional list of cities to process. If not provided, processes all cities.")
) -> Dict:
    """
    Create or update all semantic search data (embeddings and ball trees) for specified cities.
    
    This endpoint starts background tasks that create embeddings and build ball trees
    for efficient semantic similarity search.
    
    This is a one-stop solution that replaces the need to call /create-embeddings
    and /create-ball-trees separately.
    
    The tasks run asynchronously and the endpoint returns immediately with the task ID.
    
    Args:
        cities: Optional list of cities to process. If not provided, processes all cities.
        
    Returns:
        Status message and task ID
    """
    try:
        task = build_embeddings_and_ball_trees_task.delay(cities)
        
        cities_msg = "all cities" if not cities else f"cities: {', '.join(cities)}"
        
        return {
            "status": "success",
            "message": f"Started semantic search data creation for {cities_msg}",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start semantic search data creation: {str(e)}"
        )
    