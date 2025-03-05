import json
import logging
import re
import math
from collections import defaultdict
from typing import Any, Dict, List

from config import AGGREGATED_DIR, PLACES
from utils.file_utils import normalize_filename
from indexing.wildcard_handler import WildcardHandler
from nltk.stem.snowball import SnowballStemmer

class IndexManager:
    """
    Manages the construction and searching of an inverted index.
    Handles tokenization, stemming (using SnowballStemmer for Russian),
    TF-IDF scoring, and lexicon building.
    """
    def __init__(self):
        self.inverted_index = defaultdict(dict)
        self.doc_freq = defaultdict(int)
        self.total_docs = 0
        self.terms_lexicon = set()
        self.wildcard_handler = None
        self.term_kgrams = defaultdict(set)
        self.stemmer = SnowballStemmer("russian")
        self.index_file = f"{AGGREGATED_DIR}/index.json"

    def _tokenize(self, text: str) -> List[str]:
        # Supports Cyrillic and Latin; returns stemmed tokens.
        tokens = re.findall(r'\b[а-яёa-z]+\b', text.lower())
        return [self._stem(token) for token in tokens if token and token not in self._stop_words()]

    def _stem(self, word: str) -> str:
        return self.stemmer.stem(word)

    def _stop_words(self) -> set:
        # Basic Russian stop words (expandable as needed)
        return {'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 
                'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же', 
                'вы', 'за', 'бы', 'по', 'ее', 'мне'}

    def build_index(self, doc_id: str, content: str):
        """
        Builds the inverted index for a single document.
        """
        tokens = self._tokenize(content)
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1
        for token, count in tf.items():
            self.inverted_index[token][doc_id] = self.inverted_index[token].get(doc_id, 0) + count
            self.doc_freq[token] = len(self.inverted_index[token])
        self.total_docs += 1

    def _tfidf(self, token: str, doc_id: str) -> float:
        if self.total_docs == 0:
            return 0.0
        df = self.doc_freq.get(token, 0)
        idf = math.log((self.total_docs + 1) / (df + 0.5))
        tf_val = self.inverted_index.get(token, {}).get(doc_id, 0)
        return (tf_val / (tf_val + 1.0)) * idf

    def build_lexicon(self):
        """
        Builds a lexicon of terms for correction using a k-gram index.
        """
        self.terms_lexicon = set(self.inverted_index.keys())
        self.wildcard_handler = WildcardHandler(self.terms_lexicon)
        for term in self.terms_lexicon:
            padded = f"${term}$"
            for i in range(len(padded) - 2):
                self.term_kgrams[padded[i:i+3]].add(term)

    def get_content_for_indexing(self, data: Dict) -> str:
        """
        Extracts all text content from aggregated data.
        Handles Wikipedia data with potentially nested sections.
        """
        content = []
        if data.get("wikipedia"):
            content.append(data["wikipedia"].get("summary", ""))
            sections = data["wikipedia"].get("sections")
            if sections:
                flattened = self._flatten_sections(sections)
                content.extend(flattened)
        if data.get("otm"):
            for item in data["otm"]:
                content.append(item.get("title", ""))
                content.append(item.get("description", ""))
        return " ".join(content)

    def _flatten_sections(self, sections: Any) -> List[str]:
        """
        Recursively flattens nested Wikipedia sections.
        """
        texts = []
        if isinstance(sections, dict):
            for key, value in sections.items():
                if isinstance(value, str):
                    texts.append(value)
                else:
                    texts.extend(self._flatten_sections(value))
        elif isinstance(sections, list):
            for item in sections:
                if isinstance(item, str):
                    texts.append(item)
                else:
                    texts.extend(self._flatten_sections(item))
        return texts

    def build_and_save_index(self, aggregated_data: Dict[str, Any]):
        """
        Builds the inverted index from the aggregated data and saves the index to a file.
        aggregated_data is a dict mapping normalized place to its aggregated data.
        """
        # Reset index data
        self.inverted_index = defaultdict(dict)
        self.doc_freq = defaultdict(int)
        self.total_docs = 0
        
        for doc_id, data in aggregated_data.items():
            content = self.get_content_for_indexing(data)
            self.build_index(doc_id, content)
        self.build_lexicon()
        
        index_data = {
            "inverted_index": self.inverted_index,
            "doc_freq": self.doc_freq,
            "total_docs": self.total_docs,
            "terms_lexicon": list(self.terms_lexicon)
        }
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=4)
            logging.info(f"[IndexManager] Index built and saved to {self.index_file}")
        except Exception as e:
            logging.error(f"[IndexManager] Error saving index: {e}")

    def search(self, query: str) -> List[tuple]:
        """
        Searches the inverted index for the given query and returns a list of tuples (doc_id, score).
        """
        results = defaultdict(float)
        tokens = self._tokenize(query)
        for token in tokens:
            if token in self.inverted_index:
                for doc_id in self.inverted_index[token]:
                    results[doc_id] += self._tfidf(token, doc_id)
        return sorted(results.items(), key=lambda x: x[1], reverse=True)
