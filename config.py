from pydantic_settings import BaseSettings
from typing import List, Optional

# https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
class Settings(BaseSettings):
    OPENTRIPMAP_API_KEY: str
    GOOGLE_PLACES_API: str
    TELEGRAM_BOT_API: str
    PLACES: List[str]
    # https://developers.google.com/maps/documentation/places/web-service/place-types
    PLACE_TYPES: List[str] = ["restaurant","cafe","tourist_attraction","museum","park","lodging"]
    RESOURCES: List[str] = ["wikipedia", "google_places"]
    # https://developers.google.com/maps/documentation/places/web-service/text-search#fieldmask
    FIELD_MASK: str = "places.id,places.displayName,places.location"

    USER_AGENT: str = 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0'
    LANGUAGE_CODE: str = 'ru'
    REGION_CODE: str = 'ru'
    TIMEOUT: int = 10
    RETRY_DELAY: int = 5
    MAX_RETRIES: int = 3
    MAX_DEPTH_WEB_SCRAPER: int = 2
    RESULTS_PER_PAGE: int = 5
    NUM_PAGES: int = 5
    BASE_CHECKPOINT_DIR: str = 'checkpoints'
    AGGREGATED_DIR: str = 'aggregated'
    DEBUG_MODE: bool = True


    class Config:
        env_file = ".env"


settings = Settings()