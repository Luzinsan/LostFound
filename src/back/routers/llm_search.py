from fastapi import APIRouter, HTTPException, Query, Form, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional, Annotated
import logging
import time
import json

from src.back.models.rag_models import (
    ChatMessage,
    SearchResult,
    LLM_MODEL
)
from src.core.llm.async_services import (
    chutes_api_rephrase_query,
    generate_rag_response,
    stream_rag_response
)
from src.core.llm.utils import prepare_context_from_results
from src.configs.config import settings
from src.back.routers.semantic_search import (
    semantic_search as perform_semantic_search_route
)
from src.back.routers.locations import (
    get_location_details as perform_get_location_details_route
)
router = APIRouter(
    prefix="/rag",
    tags=["rag"],
    responses={404: {"description": "Not found"}},
)


async def parse_chat_messages(
    messages_json: str = Form(..., description='JSON array of chat messages with "role" and "content" fields. Example: [{"role": "user", "content": "Tell me about places in Moscow"}]')
) -> List[ChatMessage]:
    try:
        messages_data = json.loads(messages_json)
        return [ChatMessage(
            role=msg["role"], 
            content=msg["content"]
        ) for msg in messages_data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid messages format: {str(e)}")


@router.post("/chat-completion")
async def rag_chat_completion(
    messages: List[ChatMessage] = Depends(parse_chat_messages),
    model: str = Form(default=LLM_MODEL, description="LLM model to use for generating responses"),
    temperature: float = Form(default=0.7, description="Sampling temperature (0.0-1.0)"),
    top_p: float = Form(default=1.0, description="Nucleus sampling parameter"),
    max_tokens: int = Form(default=2000, description="Maximum number of tokens to generate"),
    stream: bool = Form(default=False, description="Whether to stream the response"),
    city: Optional[str] = Form(default=None, description="City to search in"),
    types: Optional[List[str]] = Form(default=None, description="Comma-separated list of place types"),
    limit: int = Form(default=5, description="Maximum number of search results")
):
    """
    RAG (Retrieval Augmented Generation) endpoint that enhances LLM responses 
    with semantic search results for travel-related queries.
    
    Use this form to submit chat messages and other parameters to get an AI response
    based on retrieved information from the database.
    
    For the messages field, provide a JSON array in this format:
    [{"role": "user", "content": "Tell me about places in Moscow"}]
    """
    try:    
        if city == "":
            city = None
        if len(types) == 1 and types[0] == "":
            types = None
        user_messages = [msg.content for msg in messages if msg.role == "user"]
        
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user messages found in the conversation")
        
        if len(user_messages) == 1:
            user_query = user_messages[0]
        else:
            user_query = " | ".join(user_messages)
            user_query = user_query[-max_tokens:] if len(user_query) > max_tokens else user_query
        
        if not user_query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        llm_rephrased_output = await chutes_api_rephrase_query(user_query) 
        actual_rephrased_query = llm_rephrased_output.get("rephrased_query", user_query)
        if llm_rephrased_output.get("cities"):
            final_cities_for_search = llm_rephrased_output.get("cities")
        elif city:
            final_cities_for_search = city
        else:
            final_cities_for_search = settings.CITIES
        
        search_results_data = await perform_semantic_search_route(
            query=actual_rephrased_query,
            cities=[final_cities_for_search],
            types=types,
            limit=limit
        )
        search_results_data["detailed_results"] = []
        for place in search_results_data["results"]:
            detailed_place = await perform_get_location_details_route(
                place["doc_id"]
            )
            search_results_data["detailed_results"].append(detailed_place.model_dump())
        context = prepare_context_from_results(search_results_data, limit)
        system_message_content = settings.RESULT_SUMMARY_PROMPT.format(
            limit=limit,
            original_query=user_query,
            enhanced_query=actual_rephrased_query,
            results=context
        )
        messages_with_context = [
            ChatMessage(
                role="system",
                content=system_message_content
        )] + messages
        
        if stream:
            return StreamingResponse(
                stream_rag_response(messages_with_context, temperature, max_tokens),
                media_type="text/event-stream"
            )
        response = await generate_rag_response(messages_with_context, temperature, max_tokens)
        return {
            "id": f"rag-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(" ".join([m.content for m in messages_with_context]).split()),
                "completion_tokens": len(response.split()),
                "total_tokens": len(" ".join([m.content for m in messages_with_context]).split()) + len(response.split())
            },
            "search_result": search_results_data,
            "system_message_content": system_message_content
        }
    except Exception as e:
        logging.error(f"RAG completion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG completion error: {str(e)}")
