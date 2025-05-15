import re
import logging
from typing import List, Set, Optional

class WildcardHandler:
    """
    Handles wildcard queries by building k-gram indexes (forward and reverse)
    and filtering candidates based on the wildcard pattern.
    """
    def __init__(self, lexicon: Set[str], k: int = 3):
        """
        Initialize with a lexicon of terms and build k-gram indexes.
        
        Args:
            lexicon: Set of terms to index
            k: Length of k-grams (default: 3)
        """
        self.lexicon = lexicon
        self.k = k
        self.forward_index = self._build_forward_index()
        self.reverse_index = self._build_reverse_index()
        
    def _build_forward_index(self) -> dict:
        """
        Build forward k-gram index for prefix matching.
        Maps each k-gram to terms that start with it.
        """
        index = {}
        for term in self.lexicon:
            if len(term) >= self.k:
                prefix = term[:self.k]
                if prefix not in index:
                    index[prefix] = set()
                index[prefix].add(term)
        return index
        
    def _build_reverse_index(self) -> dict:
        """
        Build reverse k-gram index for suffix matching.
        Maps each reversed k-gram to terms that end with it.
        """
        index = {}
        for term in self.lexicon:
            if len(term) >= self.k:
                suffix = term[-self.k:]
                if suffix not in index:
                    index[suffix] = set()
                index[suffix].add(term)
        return index
        
    def process_query(self, query: str) -> List[str]:
        """
        Process a query with wildcards and return matching terms.
        Supports different types of wildcard patterns:
        - prefix*: Matches terms starting with prefix
        - *suffix: Matches terms ending with suffix
        - prefix*suffix: Matches terms starting with prefix and ending with suffix
        - *mid*: Matches terms containing mid
        - Regular queries without wildcards are passed through
        
        Args:
            query: The search query, possibly with wildcards
            
        Returns:
            List of matching terms from the lexicon
        """
        if not query:
            return []
            
        query = query.lower()
        
        # If no wildcard, try to find variations of the query
        if '*' not in query:
            # First try exact match
            if query in self.lexicon:
                return [query]
            
            # Try stemmed version of the query
            stemmed_query = self._stem(query)
            if stemmed_query in self.lexicon:
                return [stemmed_query]
            
            # If no matches found, return the original query
            return [query]
            
        try:
            # Handle different wildcard patterns
            if query.startswith('*') and query.endswith('*') and len(query) > 2:
                # Case: *middle* - find terms containing the middle part
                middle = query[1:-1]
                if middle:
                    return self._find_contains_matches(middle)
                    
            elif query.startswith('*'):
                # Case: *suffix - find terms ending with the suffix
                suffix = query[1:]
                return self._find_suffix_matches(suffix)
                            
            elif query.endswith('*'):
                # Case: prefix* - find terms starting with the prefix
                prefix = query[:-1]
                return self._find_prefix_matches(prefix)
                            
            else:
                # Case: prefix*suffix - find terms matching both prefix and suffix
                parts = query.split('*')
                if len(parts) == 2:
                    prefix, suffix = parts
                    return self._find_prefix_suffix_matches(prefix, suffix)
        
        except Exception as e:
            logging.error(f"Error processing wildcard query '{query}': {e}")
            # Return a limited set of terms as fallback
            return list(self.lexicon)[:100]
            
        return [query.replace('*', '')]
        
    def _stem(self, word: str) -> str:
        """
        Apply stemming to a word using SnowballStemmer for Russian.
        """
        try:
            from nltk.stem.snowball import SnowballStemmer
            stemmer = SnowballStemmer("russian")
            return stemmer.stem(word)
        except Exception as e:
            logging.error(f"Error in stemming word '{word}': {e}")
            return word
        
    def _find_prefix_matches(self, prefix: str) -> List[str]:
        """
        Find terms that start with the given prefix.
        """
        if len(prefix) >= self.k:
            prefix_gram = prefix[:self.k]
            candidates = self.forward_index.get(prefix_gram, set())
            matches = {term for term in candidates if term.startswith(prefix)}
        else:
            # Short prefix, check all terms
            matches = {term for term in self.lexicon if term.startswith(prefix)}
        
        return self._limit_matches(list(matches))
        
    def _find_suffix_matches(self, suffix: str) -> List[str]:
        """
        Find terms that end with the given suffix.
        """
        if len(suffix) >= self.k:
            suffix_gram = suffix[-self.k:]
            candidates = self.reverse_index.get(suffix_gram, set())
            matches = {term for term in candidates if term.endswith(suffix)}
        else:
            # Short suffix, check all terms
            matches = {term for term in self.lexicon if term.endswith(suffix)}
        
        return self._limit_matches(list(matches))
        
    def _find_contains_matches(self, substring: str) -> List[str]:
        """
        Find terms that contain the given substring.
        """
        pattern = f".*{re.escape(substring)}.*"
        matches = self._filter_by_regex(pattern)
        return self._limit_matches(list(matches))
        
    def _find_prefix_suffix_matches(self, prefix: str, suffix: str) -> List[str]:
        """
        Find terms that start with prefix and end with suffix.
        """
        pattern = f"^{re.escape(prefix)}.*{re.escape(suffix)}$"
        matches = self._filter_by_regex(pattern)
        return self._limit_matches(list(matches))
        
    def _limit_matches(self, matches: List[str], limit: int = 200) -> List[str]:
        """
        Limit the number of matches to prevent performance issues.
        """
        if len(matches) > limit:
            logging.warning(f"Too many matches ({len(matches)}), limiting to {limit}")
            return matches[:limit]
        return matches
        
    def _filter_by_regex(self, pattern: str) -> Set[str]:
        """
        Filter lexicon terms using a regex pattern.
        """
        try:
            regex = re.compile(pattern)
            return {term for term in self.lexicon if regex.match(term)}
        except re.error as e:
            logging.error(f"Invalid regex pattern '{pattern}': {e}")
            return set()
