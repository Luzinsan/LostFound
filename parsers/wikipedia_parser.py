# parsers/wikipedia_parser.py

import json
import os
import logging
from typing import Optional, Dict
import wikipediaapi
from parsers.base_parser import BaseParser
from utils.file_utils import normalize_filename
from config import BASE_CHECKPOINT_DIR

class WikipediaParser(BaseParser):
    # https://wikipedia-api.readthedocs.io/en/latest/
    def __init__(self, user_agent: str, language: str):
        self.wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language=language)

    def parse_sections(self, sections):
        sub_sections = {}
        for s in sections:
            data = self.parse_sections(s.sections) if s.sections else s.text[:]
            if data:
                sub_sections[s.title] = data
        return sub_sections

    def parse(self, place: str, 
              checkpoint: bool = True,
              checkpoint_dir: str = os.path.join(BASE_CHECKPOINT_DIR, "wikipedia"), 
              **kwargs) -> Optional[Dict[str, str]]:
        logging.info(f"[Wikipedia] Searching page for: {place}")
        page = self.wiki.page(place)
        if page.exists():
            logging.info(f"[Wikipedia] Found page: {page.title}")
            wiki_data = {
                "url": page.fullurl,
                "title": page.title,
                "summary": page.summary[:],
                "sections": self.parse_sections(page.sections),
            }
            if checkpoint:
                cp_filename = os.path.join(checkpoint_dir, f"wikipedia_{normalize_filename(place)}.json")
                try:
                    with open(cp_filename, "w", encoding="utf-8") as f:
                        json.dump(wiki_data, f, ensure_ascii=False, indent=4)
                    logging.info(f"[Wikipedia] Checkpoint saved: {cp_filename}")
                except Exception as e:
                    logging.error(f"[Wikipedia] Error saving checkpoint: {e}")
            return wiki_data
        else:
            logging.warning(f"[Wikipedia] Page '{place}' does not exist.")
            return None
