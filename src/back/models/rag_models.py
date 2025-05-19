from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

LLM_MODEL = "deepseek-ai/DeepSeek-R1"

class ChatMessage(BaseModel):
    """
    Represents a message in a chat conversation.
    """
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: str = Field(..., description="Content of the message")


class SearchResult(BaseModel):
    """
    Structured representation of search results with query enhancement.
    """
    original_query: str = Field(..., description="Original user query")
    enhanced_query: str = Field(..., description="Query enhanced by LLM")
    search_results: Dict = Field(..., description="Results from the search engine")
    limit: int = Field(..., description="Maximum number of results requested")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_query": "good places in Moscow",
                    "enhanced_query": "tourist attractions and recommended places to visit in Moscow",
                    "search_results": {
                        "status": "success",
                        "results": [
                            {"name": "Red Square", "description": "Famous city square"}
                        ],
                        "total_found": 1
                    },
                    "limit": 5
                }
            ]
        }
    } 