from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import logging
from config import settings
from routers import search, system, locations
from models import ErrorResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG_MODE else logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = FastAPI(
    title="Lost&Found API",
    description="""
    Lost&Found API предоставляет интерфейс для поиска различных мест и достопримечательностей в разных городах.
    
    ## Основные возможности
    
    * 🔍 Поиск мест в конкретном городе
    * 🌍 Поиск по всем доступным городам
    * 🏛️ Фильтрация по типам мест (музеи, рестораны, парки и т.д.)
    * 📊 Получение статистики и системной информации
    * 📄 Пагинация и фильтрация списка мест
    * ℹ️ Подробная информация о каждом месте
    
    ## Типы мест
    
    * Рестораны и кафе
    * Музеи и галереи
    * Парки и зоны отдыха
    * Театры и концертные залы
    * Исторические достопримечательности
    
    ## Использование
    
    API поддерживает различные параметры поиска и фильтрации. Для получения подробной информации 
    о каждом эндпоинте используйте интерактивную документацию ниже.
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
    search.router,
    prefix="/api/v1",
    tags=["search"]
)
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
            "name": "search",
            "description": "Операции поиска мест и достопримечательностей",
        },
        {
            "name": "system",
            "description": "Системные операции и управление",
        },
        {
            "name": "locations",
            "description": "Управление и получение информации о местах",
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", tags=["root"])
async def root():
    return {
        "message": "Добро пожаловать в Lost&Found API",
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
    logging.error(f"Необработанное исключение: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Произошла непредвиденная ошибка",
            status_code=500
        ).dict()
    ) 