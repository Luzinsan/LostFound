import json
import logging
import re
import math
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from config import AGGREGATED_DIR, PLACES
from utils.file_utils import normalize_filename
from indexing.wildcard_handler import WildcardHandler
from nltk.stem.snowball import SnowballStemmer

class IndexManager:
    """
    Manages the construction and searching of inverted indexes, now city-specific.
    Handles tokenization, stemming (using SnowballStemmer for Russian),
    TF-IDF scoring, and lexicon building for each city separately.
    """
    def __init__(self):
        self.city_indexes = {} # Dictionary to hold indexes for each city
        self.stemmer = SnowballStemmer("russian")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizes text, supports Cyrillic and Latin, and applies stemming.
        """
        tokens = re.findall(r'\b[а-яёa-z]+\b', text.lower())
        return [self._stem(token) for token in tokens if token and token not in self._stop_words()]

    def _stem(self, word: str) -> str:
        """
        Applies stemming to a word using SnowballStemmer for Russian.
        """
        return self.stemmer.stem(word)

    def _stop_words(self) -> set:
        """
        Returns a set of basic Russian stop words. Expandable as needed.
        """
        return {'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а',
                'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же',
                'вы', 'за', 'бы', 'по', 'ее', 'мне'}

    def build_index(self, city_name: str, doc_id: str, content: str):
        """
        Builds the inverted index for a single document within a specific city.
        """
        if city_name not in self.city_indexes:
            self.city_indexes[city_name] = {
                "inverted_index": defaultdict(dict),
                "doc_freq": defaultdict(int),
                "total_docs": 0,
                "terms_lexicon": set(),
                "wildcard_handler": None,
                "term_kgrams": defaultdict(set)
            }
        city_index = self.city_indexes[city_name]
        inverted_index = city_index["inverted_index"]

        tokens = self._tokenize(content)
        tf = defaultdict(int)
        for token in tokens:
            tf[token] += 1
        for token, count in tf.items():
            inverted_index[token][doc_id] = inverted_index[token].get(doc_id, 0) + count
        city_index["total_docs"] += 1


    def _tfidf(self, city_name: str, token: str, doc_id: str) -> float:
        """
        Calculates TF-IDF score for a token in a document within a city.
        """
        if city_name not in self.city_indexes:
            return 0.0
        city_index = self.city_indexes[city_name]
        total_docs = city_index["total_docs"]
        doc_freq = city_index["doc_freq"]
        inverted_index = city_index["inverted_index"]

        if total_docs == 0:
            return 0.0
        df = doc_freq.get(token, 0)
        idf = math.log((total_docs + 1) / (df + 0.5))
        tf_val = inverted_index.get(token, {}).get(doc_id, 0)
        return (tf_val / (tf_val + 1.0)) * idf

    def build_lexicon(self, city_name: str):
        """
        Builds a lexicon of terms for correction using a k-gram index for a specific city.
        """
        if city_name not in self.city_indexes:
            return
        city_index = self.city_indexes[city_name]
        inverted_index = city_index["inverted_index"]

        city_index["terms_lexicon"] = set(inverted_index.keys())
        city_index["wildcard_handler"] = WildcardHandler(city_index["terms_lexicon"])
        term_kgrams = city_index["term_kgrams"]
        for term in city_index["terms_lexicon"]:
            padded = f"${term}$"
            for i in range(len(padded) - 2):
                term_kgrams[padded[i:i+3]].add(term)

    def get_content_for_indexing(self, attraction_data: Dict) -> str:
        """
        Extracts text content from attraction data for indexing.
        """
        content = []
        content.append(attraction_data.get("name", ""))
        if attraction_data.get("wikipedia_extracts"):
            content.append(attraction_data["wikipedia_extracts"].get("summary", ""))
            sections = attraction_data["wikipedia_extracts"].get("sections")
            if sections:
                flattened = self._flatten_sections(sections)
                content.extend(flattened)
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

    def build_and_save_index(self, city_name: str, aggregated_city_data: Dict[str, Any]):
        """
        Builds the inverted index for a specific city from the aggregated data and saves it to a file.
        aggregated_city_data is the aggregated data for a single city.
        """
        logging.info(f"[IndexManager] Building index for city: {city_name}")
        # Reset index data for this city
        self.city_indexes[city_name] = {
            "inverted_index": defaultdict(dict),
            "doc_freq": defaultdict(int),
            "total_docs": 0,
            "terms_lexicon": set(),
            "wildcard_handler": None,
            "term_kgrams": defaultdict(set)
        }

        for attraction_data in aggregated_city_data['otm']:
            if name_attract := attraction_data.get("name"): # Use name as name_attract
                content = self.get_content_for_indexing(attraction_data)
                self.build_index(city_name, name_attract, content)
            else:
                logging.warning(f"[IndexManager] Attraction without xid found in {city_name}, skipping.")

        city_index = self.city_indexes[city_name]
        city_index["doc_freq"] = self._calculate_doc_freq(city_index["inverted_index"]) # Calculate doc_freq after building index
        self.build_lexicon(city_name)

        index_data = {
            "inverted_index": city_index["inverted_index"],
            "doc_freq": city_index["doc_freq"],
            "total_docs": city_index["total_docs"],
            "terms_lexicon": list(city_index["terms_lexicon"])
        }
        index_dir = os.path.join(AGGREGATED_DIR, "city_indexes")
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        index_file = os.path.join(index_dir, f"index_{normalize_filename(city_name)}.json")
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, ensure_ascii=False, indent=4)
            logging.info(f"[IndexManager] Index for {city_name} built and saved to {index_file}")
        except Exception as e:
            logging.error(f"[IndexManager] Error saving index for {city_name}: {e}")

    def _calculate_doc_freq(self, inverted_index):
        """Calculates document frequency for all terms in the inverted index."""
        doc_freq = defaultdict(int)
        for term, postings in inverted_index.items():
            doc_freq[term] = len(postings)
        return doc_freq


    def load_index(self, city_name: str) -> bool:
        """
        Loads the inverted index for a specific city from file.
        Returns True if loaded successfully, False otherwise.
        """
        index_dir = os.path.join(AGGREGATED_DIR, "city_indexes")
        index_file = os.path.join(index_dir, f"index_{normalize_filename(city_name)}.json")
        if not os.path.exists(index_file):
            logging.warning(f"[IndexManager] Index file for {city_name} not found: {index_file}")
            return False
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            self.city_indexes[city_name] = {
                "inverted_index": defaultdict(dict, {k: v for k, v in index_data["inverted_index"].items()}), # Convert back to defaultdict
                "doc_freq": defaultdict(int, index_data["doc_freq"]), # Convert back to defaultdict
                "total_docs": index_data["total_docs"],
                "terms_lexicon": set(index_data["terms_lexicon"]),
                "wildcard_handler": WildcardHandler(set(index_data["terms_lexicon"])), # Rebuild wildcard handler
                "term_kgrams": defaultdict(set) # k-grams are not saved for now, rebuild if needed for suggestions
            }
            logging.info(f"[IndexManager] Index for {city_name} loaded from {index_file}")
            return True
        except Exception as e:
            logging.error(f"[IndexManager] Error loading index for {city_name} from {index_file}: {e}")
            return False


    def search(self, city_name: str, query: str) -> List[tuple]:
        """
        Searches the inverted index for the given query within a specific city and returns a list of tuples (doc_id, score).
        """
        if city_name not in self.city_indexes or not self.city_indexes[city_name]["inverted_index"]:
            logging.warning(f"[IndexManager] No index loaded for city: {city_name}. Please load index first.")
            return []

        city_index = self.city_indexes[city_name]
        inverted_index = city_index["inverted_index"]
        results = defaultdict(float)
        # tokens = self._tokenize(query)
        wildcard_handler = WildcardHandler(city_index['terms_lexicon'])
        tokens = wildcard_handler.process_query(query)
        for token in tokens:
            if token in inverted_index:
                for doc_id in inverted_index[token]:
                    results[doc_id] += self._tfidf(city_name, token, doc_id)
        return sorted(results.items(), key=lambda x: x[1], reverse=True)