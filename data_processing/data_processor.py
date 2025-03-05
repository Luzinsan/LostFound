import re
from typing import List

class DataProcessor:
    def __init__(self, keywords: List[str]):
        self.keywords = keywords

    def process_text(self, text: str) -> List[str]:
        cleaned_text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'[.!?]', cleaned_text)
        interesting_sentences = sentences
        return interesting_sentences
