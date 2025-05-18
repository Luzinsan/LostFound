import os
from typing import List
from pydantic_settings import BaseSettings

# https://docs.pydantic.dev/latest/concepts/pydantic_settings/#usage
class Settings(BaseSettings):
    OPENTRIPMAP_API_KEY: str = ''
    GOOGLE_PLACES_API: str = ''
    TELEGRAM_BOT_API: str = ''
    CHUTES_API_KEY: str = ''
    CHUTES_LLM_API_URL: str = 'https://llm.chutes.ai/v1/chat/completions'
    API_BASE: str = '/api/v1'
    CITIES: List[str] = ["Москва", "Санкт-Петербург", "Нижний Новгород"]
    # https://developers.google.com/maps/documentation/places/web-service/place-types
    PLACE_TYPES: List[str] = ["restaurant","cafe","tourist_attraction","museum","performing_arts_theater","historical_place","art_gallery","park","lodging","church"]
    RESOURCES: List[str] = ["cities", "google_places"]
    # https://developers.google.com/maps/documentation/places/web-service/text-search#fieldmask
    FIELD_MASK: str = "places.id,places.displayName,places.location"
    BOOLEAN_FIELDS: str = ""

    USER_AGENT: str = 'Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0'
    LANGUAGE_CODE: str = 'ru'
    REGION_CODE: str = 'ru'
    TIMEOUT: int = 10
    RETRY_DELAY: int = 5
    MAX_RETRIES: int = 3
    MAX_DEPTH_WEB_SCRAPER: int = 2
    MAX_LINKS: int = 3
    MAX_PARAGRAPHS: int = 20
    SPELL_CHECKER_MAX_DISTANCE: int = 5
    RESULTS_PER_PAGE: int = 5
    NUM_PAGES: int = 5
    BASE_CHECKPOINT_DIR: str = 'checkpoints'
    AGGREGATED_DIR: str = 'aggregated'
    DEBUG_MODE: bool = True

    MONGO_URI: str = 'mongodb://localhost:27017/'
    MONGO_DB_NAME: str = 'lost_found'
    BROKER_URL: str = 'redis://localhost:6379/0'
    RESULT_BACKEND: str = 'redis://localhost:6379/0'


    QUERY_REPHRASE_PROMPT: str = """
**Role:** You are a highly specialized AI assistant. Your purpose is to process user queries about locations within Russia and prepare them for a semantic search system. Accuracy, adherence to format, and efficiency are paramount.

**Primary Task:**
Analyze the provided user query. Your objective is to extract two key pieces of information and present them in a specific single-line format:
1.  **Rephrased Query for Semantic Search:** Transform the original user query into a concise, semantically rich search query in **Russian**.
    *   This rephrased query **MUST NOT contain any explicit city names**. City-based filtering is handled separately by the system.
    *   Focus on *what* the user is looking for (e.g., type of place, specific features, desired atmosphere, activities).
    *   The rephrased query must be entirely in **Russian**.
    *   Preserve the core meaning and intent of the original query.
    *   Incorporate relevant keywords, descriptive attributes, and contextual details to enhance semantic understanding.
    *   It should be a single, coherent phrase or question, optimized for conciseness and semantic density.
2.  **Extracted City Names:** Identify and list all **Russian city names** mentioned in the user query.
    *   If multiple cities are mentioned, list them separated by a comma (e.g., "Москва,Санкт-Петербург").
    *   If no Russian cities are mentioned, use the exact keyword `NONE`.

**Output Format Specification:**
Your entire response **MUST BE a single line of text**. There should be **NO newline characters** (`\n`) in your output.
The single line must strictly follow this structure:

`[Rephrased Russian Query]|||[Comma-separated Russian Cities or NONE]`

**Key Formatting Rules:**
*   The `[Rephrased Russian Query]` comes first.
*   This is followed immediately by the delimiter: `|||` (three pipe characters).
*   This is followed immediately by the `[Comma-separated Russian Cities or NONE]`.
*   There should be **NO spaces** immediately before or after the `|||` delimiter unless they are naturally part of the rephrased query or the city names themselves.
*   Do not add any explanations, introductory text, or any content other than the single structured line.

**Examples:**

Original Query: "places in Moscow to walk with kids"
Expected Output: `парки и скверы для прогулок с детьми с игровыми площадками и развлечениями|||Москва`

Original Query: "best historical museums in Saint Petersburg and Kazan"
Expected Output: `главные исторические музеи с богатой экспозицией и уникальными артефактами|||Санкт-Петербург,Казань`

Original Query: "cheap restaurants with Russian cuisine"
Expected Output: `недорогие рестораны традиционной русской кухни с аутентичной атмосферой|||NONE`

Original Query: "куда сходить в Екатеринбурге вечером недорого"
Expected Output: `бюджетные варианты вечернего досуга и развлечений|||Екатеринбург`

Original Query: "interesting places for photo shoots"
Expected Output: `живописные и необычные локации для фотосъемок с красивыми видами|||NONE`

Original Query: "What to see in Volgograd and Saratov if I like history?"
Expected Output: `исторические достопримечательности и памятные места для любителей истории|||Волгоград,Саратов`

**User Query to Process:**
{query}
"""

    RESULT_SUMMARY_PROMPT: str = """
**Role:** You are an intelligent AI assistant. Your primary function is to synthesize information from provided search results and present it to a user in a helpful, engaging, and informative way. You need to act as a knowledgeable local guide.

**Core Task:**
Analyze the top `limit` search results provided in the `results` context. Your goal is to craft a detailed, natural language response in **Russian** for the user. This response should:
1.  Acknowledge the user's original query (`original_query`).
2.  Summarize the most relevant information about the found places.
3.  Rank the places from most relevant to least relevant based on your understanding of the `original_query` and the `enhanced_query`, and the details in `results`.
4.  For each recommended place, include:
    *   Its **Name** and its **unique identifier (`doc_id`)**. The `doc_id` is critical. You will find it in the context after `[Place ` and before `]:`. Ensure this `doc_id` is clearly associated with the place you are describing, for example by stating "Name (ID: doc_id)" or in a similar clear fashion.
    *   A brief, engaging **description** of the place. You can draw from its `Address`, `Types`, and `Other information`.
    *   A compelling **reason why this place might be interesting or relevant** to the user, specifically connecting it to their query. Leverage the `Reviews` and `Other information` sections heavily for this. Highlight unique aspects or positive sentiments from reviews.
5.  The final output should be a coherent text, not a raw data dump.

**Understanding the Input Context (`results`):**
The `results` variable will provide a formatted string. Here's how to interpret it:
*   It starts with a line indicating the `City: [City Name]`.
*   Then, for each search result, there are several lines of information:
    *   `[Place doc_id]: Place Name` (This `doc_id` is the unique identifier you MUST use and reference for each place.)
    *   `Address: address`
    *   `Types: comma-separated list of types`
    *   `Other information: keywords, descriptions, or other details from the source`
    *   `Reviews: flattened string of user reviews, often with ratings and timestamps`
    *   An empty line often separates entries.

**Instructions for your Response:**
*   **Language:** The entire response to the user MUST be in **Russian**.
*   **Tone:** Friendly, helpful, conversational, and informative.
*   **Structure:**
    *   Start with a brief introductory sentence that acknowledges the user's query (e.g., "Based on your interest in 'original_query' in [City Name], here are some places you might find interesting:").
    *   Present the ranked list of places. You can use a numbered list or clear paragraph breaks for each place.
    *   For each place, make sure to explicitly mention its Name and its `doc_id` as extracted from the `[Place doc_id]:` line in the context. For example: "1. Название Места (ID: ChIJAS4uY1pKtUYR7QsT38a1y6s)".
    *   Synthesize information; do not just copy-paste long review texts. Extract the essence.
    *   Focus on what makes each place special or a good fit for the user.
*   **Ranking Logic:** Your ranking should be based on how well each place seems to match the `original_query` and `enhanced_query`, considering all available data in `results` (types, other info, reviews).
*   **Conciseness:** Be informative but avoid unnecessary verbosity.
*   **Do Not:**
    *   Output raw JSON or the `results` string directly.
    *   Include any meta-commentary about your process unless specifically asked.
    *   Forget to mention the `doc_id` for each place.

**Input Variables You Will Receive:**
*   `limit`: The maximum number of top search results to analyze and include.
*   `original_query`: The user's original request in their own words.
*   `enhanced_query`: The system-rephrased query used for the semantic search.
*   `results`: The formatted string containing search result details as described above.

**Example of how to reference a place (Remember the output needs to be in Russian):**
"Одно из интересных мест - **Нулевой километр (ID: ChIJAS4uY1pKtUYR7QsT38a1y6s)**. Он находится по адресу: пр-д Воскресенские Ворота, 1А. Это популярная туристическая достопримечательность, символизирующая начало всех дорог России. Судя по отзывам, многие туристы считают это знаковым местом на Красной площади и отмечают его историческую важность..."

---
User's Original Query: `{original_query}`
System's Enhanced Query: `{enhanced_query}`
Number of Top Results to Consider: `{limit}`

Search Results Context:
{results}
---
Now, generate the response for the user.
"""

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")


settings = Settings()