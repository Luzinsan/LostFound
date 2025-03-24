from config import settings
import logging
from typing import Optional, Dict
import wikipediaapi
from parsers.base_parser import BaseParser
from config import settings
import time
from utils.mongodb_handler import mongo_manager

class WikipediaParser(BaseParser):
    # https://wikipedia-api.readthedocs.io/en/latest/
    def __init__(self, user_agent: str = settings.USER_AGENT):
        self.wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language=settings.LANGUAGE_CODE)

    def parse_sections(self, sections):
        sub_sections = {}
        for s in sections:
            data = self.parse_sections(s.sections) if s.sections else s.text[:]
            if data:
                sub_sections[s.title] = data
        return sub_sections

    def parse(self, city: str
              ) -> Optional[Dict[str, str]]:
        logging.info(f"[Wikipedia] Searching page for: {city}")
        page = self.wiki.page(city)
        if page.exists():
            logging.info(f"[Wikipedia] Found page: {page.title}")
            wiki_data = {
                "city": city, 
                "wikipedia": {
                    "url": page.fullurl,
                    "title": page.title,
                    "summary": page.summary[:],
                    "sections": self.parse_sections(page.sections),
                }, 
                "timestamp": time.time()
                }
            mongo_manager.save(wiki_data, "wikipedia")
            return wiki_data
        else:
            logging.warning(f"[Wikipedia] Page '{city}' does not exist.")
            return None
