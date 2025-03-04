import json
import logging
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urlencode

class YandexMapsReviewsParser:
    """
    YandexMapsReviewsParser scrapes reviews from Yandex Maps for a given attraction.
    It builds a search URL based on the attraction name and optionally coordinates,
    retrieves the HTML content, and parses review elements.
    
    Note: CSS selectors used for review extraction are examples and may need adjustment 
    based on the current page structure of Yandex Maps.
    """
    def __init__(self, user_agent: str = None, timeout: int = 15):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36")
        })
        self.timeout = timeout

    def get_reviews(self, attraction_name: str, point: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        """
        Retrieves reviews from Yandex Maps for the given attraction.
        Constructs a search URL based on the attraction name and optional coordinates.
        Returns a list of review dictionaries with fields such as review_text, reviewer_name, and rating.
        """
        reviews = []
        # Build query parameters for Yandex Maps search.
        # For better accuracy, include additional details if coordinates are provided.
        query = attraction_name
        
        params = {"text": query}
        base_url = "https://yandex.ru/maps/"
        search_url = base_url + "?" + urlencode(params)
        logging.info(f"[YandexMaps] Searching reviews at: {search_url}")
        try:
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            # TODO: Пошарить яндекс карту. Там есть отзывы, нужно только найти селекторы чтобы извлечь информацию
            # These selectors are hypothetical – adjust them based on actual page inspection.
            review_elements = soup.select("div.business-reviews-card-view__reviews-container")
            for element in review_elements:
                review_text = element.get_text(strip=True)
                reviewer_elem = element.select_one("span.reviewer-name")
                reviewer_name = reviewer_elem.get_text(strip=True) if reviewer_elem else ""
                rating_elem = element.select_one("span.review-rating")
                rating = rating_elem.get_text(strip=True) if rating_elem else ""
                reviews.append({
                    "review_text": review_text,
                    "reviewer_name": reviewer_name,
                    "rating": rating
                })
            logging.info(f"[YandexMaps] Found {len(reviews)} reviews for '{attraction_name}'.")
        except Exception as e:
            # if point.get("lat") and point.get("lon"):
            # query += f" {point.get('lat')},{point.get('lon')}"
            logging.error(f"[YandexMaps] Error retrieving reviews for '{attraction_name}': {e}")
        
        return reviews
