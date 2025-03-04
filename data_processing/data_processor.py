# data_processing/data_processor.py

import re
from typing import List

class DataProcessor:
    def __init__(self, keywords: List[str]):
        self.keywords = keywords

    def process_text(self, text: str) -> List[str]:
        cleaned_text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'[.!?]', cleaned_text)
        interesting_sentences = sentences
        # [
        #     sentence.strip() for sentence in sentences
        #     if any(keyword in sentence.lower() for keyword in self.keywords)
        # ]
        return interesting_sentences
