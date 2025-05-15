import logging
from typing import Optional, Dict
import wikipediaapi
import time
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.core.parsers.base_parser import BaseParser
from src.configs.config import settings
from src.utils.mongodb_handler import mongo_manager
from src.configs.config import settings


class WikipediaParser(BaseParser):
    # https://wikipedia-api.readthedocs.io/en/latest/
    def __init__(self, user_agent: str = settings.USER_AGENT):
        self.wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language=settings.LANGUAGE_CODE)

    def parse_sections(self, sections: wikipediaapi.WikipediaPageSection) -> str:
        sub_sections = []
        for s in sections:
            data = self.parse_sections(s.sections) if s.sections else s.text
            if data:
                sub_sections.append(s.title + ' ' + data)
        return self.clean_string(' '.join(sub_sections))

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
                    "summary": page.summary,
                    "sections": self.parse_sections(page.sections), 
                }, 
                "timestamp": time.time()
                }
            wiki_data['search_text'] = page.title \
                               + ' ' + page.summary \
                               + ' ' + wiki_data['wikipedia']['sections']
            mongo_manager.save(wiki_data, "cities")
            return wiki_data
        else:
            logging.warning(f"[Wikipedia] Page '{city}' does not exist.")
            return None
