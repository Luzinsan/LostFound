import logging
import re
import math
import nltk
from nltk.stem.snowball import SnowballStemmer
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union, Tuple

import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.core.parsers import google_places
from src.core.indexing_search.wildcard_handler import WildcardHandler
from src.core.indexing_search.spell_checker import SpellChecker
from src.utils.mongodb_handler import MongoDBManager
from src.configs.config import settings



class IndexManager:
    """
    Manages the construction and searching of inverted indexes, now city-specific.
    Handles tokenization, stemming (using SnowballStemmer for Russian),
    TF-IDF scoring, and lexicon building for each city separately.
    """
    def __init__(self):
        self.city_indexes = {}
        self.stemmer = SnowballStemmer("russian")
        self._download_nltk_resources()
        self.stop_words = self._load_stop_words()

    def _download_nltk_resources(self):
        """Download required NLTK resources if not already present."""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')


    def _load_stop_words(self) -> set:
        """
        Loads stop words from NLTK corpus.
        Returns a set of stop words.
        """
        try:
            from nltk.corpus import stopwords
            russian_stopwords = set(stopwords.words('russian'))
            logging.info("Successfully loaded Russian stop words from NLTK")
            return russian_stopwords
        except Exception as e:
            logging.error(f"Error loading stop words from NLTK: {e}")
            return set()


    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenizes text, supports Cyrillic and Latin, and applies stemming.
        """
        try:
            text = re.sub(r'[^а-яёa-z\s]', ' ', text.lower())
            tokens = [word for word in text.split() if word and len(word) >= 3 and word not in self.stop_words]
            return [self._stem(token) for token in tokens]
        except Exception as e:
            logging.error(f"Error in tokenization: {e}")
            return []


    def _stem(self, word: str) -> str:
        """
        Applies stemming to a word using SnowballStemmer for Russian.
        """
        try:
            return self.stemmer.stem(word)
        except Exception as e:
            logging.error(f"Error in stemming word '{word}': {e}")
            return word

    def build_index(self, city_name: str, doc_id: str, search_text: str):
        """
        Builds the inverted index for a single document within a specific city using search_text.
        """
        try:
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

            tokens = self._tokenize(search_text)
            if not tokens:
                logging.warning(f"No valid tokens found in search_text for document {doc_id}")
                return
            
            for token in tokens:
                inverted_index[token][doc_id] = inverted_index[token].get(doc_id, 0) + 1
                city_index["doc_freq"][token] = len(inverted_index[token])
            
            city_index["total_docs"] += 1
            city_index["terms_lexicon"].update(tokens)
        except Exception as e:
            logging.error(f"Error building index for document {doc_id} in city {city_name}: {e}")


    def _tfidf(self, city_name: str, token: str, doc_id: str) -> float:
        """
        Calculates TF-IDF score for a token in a document within a city.
        """
        try:
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
            
            # BM25-inspired scoring
            k1 = 1.2
            b = 0.75
            avg_doc_length = sum(len(postings) for postings in inverted_index.values()) / total_docs
            doc_length = sum(len(postings) for postings in inverted_index.values())
            
            tf_score = (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * (doc_length / avg_doc_length)))
            return tf_score * idf
        except Exception as e:
            logging.error(f"Error calculating TF-IDF for token {token} in document {doc_id}: {e}")
            return 0.0


    def build_lexicon(self, city_name: str):
        """
        Builds a lexicon of terms for correction using a k-gram index for a specific city.
        """
        try:
            if city_name not in self.city_indexes:
                return
            
            city_index = self.city_indexes[city_name]
            terms_lexicon = city_index["terms_lexicon"]
            
            city_index["wildcard_handler"] = WildcardHandler(terms_lexicon)
            
            term_kgrams = city_index["term_kgrams"]
            for term in terms_lexicon:
                padded = f"${term}$"
                for i in range(len(padded) - 2):
                    term_kgrams[padded[i:i+3]].add(term)
        except Exception as e:
            logging.error(f"Error building lexicon for city {city_name}: {e}")


    def build_and_save_index(self, city_name: str, locations_data: List[Dict[str, Any]], mongo_manager: MongoDBManager):
        """
        Builds the inverted index for a specific city from the aggregated location data and saves it to MongoDB.
        """
        try:
            logging.info(f"[IndexManager] Building index for city: {city_name}")
            
            self.city_indexes[city_name] = {
                "inverted_index": defaultdict(dict),
                "doc_freq": defaultdict(int),
                "total_docs": 0,
                "terms_lexicon": set(),
                "wildcard_handler": None,
                "term_kgrams": defaultdict(set)
            }

            for location_data in locations_data:
                search_text = location_data.get('search_text', '') #+ ' ' + location_data.get('reviews_flattened', '')
                if not search_text:
                    search_text = google_places.GooglePlacesParser(
                        api_key=settings.GOOGLE_PLACES_API).generate_search_text(location_data)
                    location_data['search_text'] = search_text
                    mongo_manager.save(location_data, "places")
                    search_text += ' ' + location_data.get('reviews_flattened', '')
                
                self.build_index(city_name, location_data['_id'], search_text)

            self.build_lexicon(city_name)

            index_data = {
                "_id": f"cidx_{city_name}",
                "inverted_index": dict(self.city_indexes[city_name]["inverted_index"]),
                "doc_freq": dict(self.city_indexes[city_name]["doc_freq"]),
                "total_docs": self.city_indexes[city_name]["total_docs"],
                "terms_lexicon": list(self.city_indexes[city_name]["terms_lexicon"])
            }

            mongo_manager.save(index_data, "city_indices")
            logging.info(f"[IndexManager] Index for {city_name} built and saved to MongoDB")
        except Exception as e:
            logging.error(f"[IndexManager] Error building and saving index for {city_name}: {e}")


    def load_index(self, city_name: str, mongo_manager: MongoDBManager) -> bool:
        """
        Loads the inverted index for a specific city from MongoDB.
        Returns True if loaded successfully, False otherwise.
        """
        try:
            index_data = mongo_manager.load({"_id": f"cidx_{city_name}"}, "city_indices")
            if not index_data:
                logging.warning(f"[IndexManager] Index for {city_name} not found in MongoDB.")
                return False

            index_data = index_data[0]
            self.city_indexes[city_name] = {
                "inverted_index": defaultdict(dict, index_data["inverted_index"]),
                "doc_freq": defaultdict(int, index_data["doc_freq"]),
                "total_docs": index_data["total_docs"],
                "terms_lexicon": set(index_data["terms_lexicon"]),
                "wildcard_handler": WildcardHandler(set(index_data["terms_lexicon"])),
                "term_kgrams": defaultdict(set)
            }
            
            self.build_lexicon(city_name)
            
            logging.info(f"[IndexManager] Index for {city_name} loaded from MongoDB")
            return True
        except Exception as e:
            logging.error(f"[IndexManager] Error loading index for {city_name} from MongoDB: {e}")
            return False


    def search(self, city_name: str, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Searches the inverted index for the given query within a specific city.
        Returns a tuple containing:
        - A list of dictionaries containing document information and scores.
        - A list of tokens from the query.
        """
        try:
            if city_name not in self.city_indexes or not self.city_indexes[city_name]["inverted_index"]:
                logging.warning(f"[IndexManager] No index loaded for city: {city_name}. Please load index first.")
                return []

            city_index = self.city_indexes[city_name]
            inverted_index = city_index["inverted_index"]
            results = defaultdict(float)
            
            spell_checker = SpellChecker(city_index['terms_lexicon'])
            
            corrected_query = spell_checker.correct_query(query)
            if corrected_query != query:
                logging.info(f"Query corrected from '{query}' to '{corrected_query}'")
            
            wildcard_handler = WildcardHandler(city_index['terms_lexicon'])
            tokens = wildcard_handler.process_query(corrected_query)
            
            for token in tokens:
                if token in inverted_index:
                    for doc_id in inverted_index[token]:
                        results[doc_id] += self._tfidf(city_name, token, doc_id)
            
            return [
                {
                    "doc_id": doc_id,
                    "score": score,
                    "city": city_name
                }
                for doc_id, score in sorted(results.items(), key=lambda x: x[1], reverse=True)
            ], tokens
        except Exception as e:
            logging.error(f"[IndexManager]: Error searching index for query '{query}' in city {city_name}: {e}")
            return []
        