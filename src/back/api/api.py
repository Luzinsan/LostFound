from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import logging
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings
from src.back.routers import index_search, system, locations, semantic_search, parsing, llm_search
from src.back.models.models import ErrorResponse

logging.basicConfig(
    level=logging.INFO if settings.DEBUG_MODE else logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = FastAPI(
    title="Lost&Found API",
    description="""
    # 🌟 Lost&Found API: Advanced Search Engine for Places and Landmarks 🌟
    
    Welcome to the Lost&Found API, a powerful and versatile search engine designed to help you discover interesting places and landmarks across multiple cities. Our API combines cutting-edge search technologies to deliver fast, accurate, and contextually relevant results.
    
    ## 🔍 Advanced Search Technologies
    
    ### 📚 Inverted Index Search
    Our traditional search engine uses sophisticated inverted index technology to provide lightning-fast keyword-based searches. This approach excels at:
    * Precise matching of place names, addresses, and descriptions
    * Efficient filtering by place types and categories
    * Support for wildcard searches and partial matches
    * Optimized for exact queries and structured data
    
    ### 🧠 Semantic Search with Embeddings
    Our semantic search engine leverages state-of-the-art embedding technology to understand the meaning behind your queries, not just the keywords. This powerful approach enables:
    * Natural language understanding for more intuitive searches
    * Finding places based on concepts and ideas, not just exact terms
    * Discovering semantically related places even when using different words
    * Understanding context and intent behind your search queries
    
    ## 🌍 Comprehensive Coverage
    
    * 🔍 Search places in a specific city
    * 🌐 Search across all available cities
    * 🏛️ Filter by place types (museums, restaurants, parks, etc.)
    * 📊 Get statistics and system information
    * 📄 Pagination and place list filtering
    * ℹ️ Detailed information about each place
    
    ## 🏢 Place Types
    
    * 🍽️ Restaurants and cafes
    * 🏛️ Museums and galleries
    * 🌳 Parks and recreation areas
    * 🎭 Theaters and concert halls
    * ⛪ Historical landmarks
    
    ## 🚀 Performance & Scalability
    
    Our search engines are built for performance and scalability:
    * Inverted index search delivers results in milliseconds
    * Ball tree structure enables efficient similarity search
    * Distributed architecture handles high query volumes
    * Caching mechanisms for frequently accessed data
    
    ## 📖 Usage
    
    The API supports various search and filtering parameters. For detailed information 
    about each endpoint, use the interactive documentation below.
    """,
    version="1.0.0",
    contact={
        "name": "Lost&Found Team",
        "url": "https://github.com/yourusername/LostFound",
        "email": "your.email@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url=None,
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
        "filter": True,
        "syntaxHighlight.theme": "monokai"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    system.router,
    prefix="/api/v1",
    tags=["system"]
)
app.include_router(
    locations.router,
    prefix="/api/v1",
    tags=["locations"]
)
app.include_router(
    index_search.router,
    prefix="/api/v1",
    tags=["index_search"]
)
app.include_router(
    semantic_search.router,
    prefix="/api/v1",
    tags=["semantic_search"]
)
app.include_router(
    llm_search.router,
    prefix="/api/v1",
    tags=["rag"]
)
app.include_router(
    parsing.router,
    prefix="/api/v1",
    tags=["parsing"]
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["tags"] = [
        {
            "name": "system",
            "description": "System operations and management",
        },
        {
            "name": "locations",
            "description": "Management and information retrieval about places",
        },
        {
            "name": "index_search",
            "description": "Lightning-fast keyword-based search using inverted index technology",
        },
        {
            "name": "semantic_search",
            "description": "Intelligent semantic search using embedding technology and ball tree structure",
        },
        {
            "name": "parsing",
            "description": "API endpoints for data parsing operations and tasks management",
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Welcome to Lost&Found API",
        "version": app.version,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        }
    }

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="An unexpected error occurred",
            status_code=500
        )
    )

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    icon_path = os.path.join("static", "favicon.ico")
    
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/x-icon")
    else:
        return Response(status_code=204) 
    


