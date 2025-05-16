import logging
from typing import List, Set, Optional
from nltk.metrics.distance import edit_distance
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.configs.config import settings


class SpellChecker:
    """
    Handles spell checking using Levenshtein distance and the existing lexicon.
    """
    def __init__(self, lexicon: Set[str], max_distance: int = settings.SPELL_CHECKER_MAX_DISTANCE):
        """
        Initialize with a lexicon of terms.
        
        Args:
            lexicon: Set of terms to use for spell checking
            max_distance: Maximum Levenshtein distance for suggestions
        """
        self.lexicon = lexicon
        self.max_distance = max_distance
        

    def get_suggestions(self, word: str) -> List[str]:
        """
        Get spelling suggestions for a word using Levenshtein distance.
        
        Args:
            word: The word to get suggestions for
            
        Returns:
            List of suggested corrections, sorted by distance
        """
        if not word or word in self.lexicon:
            return []
            
        suggestions = []
        for term in self.lexicon:
            distance = edit_distance(word, term)
            if distance <= self.max_distance:
                suggestions.append((term, distance))
                
        return [term for term, _ in sorted(suggestions, key=lambda x: x[1])]
        
    def correct_query(self, query: str) -> str:
        """
        Correct spelling in a query by replacing misspelled words with suggestions.
        
        Args:
            query: The search query to correct
            
        Returns:
            Corrected query string
        """
        words = query.split()
        corrected_words = []
        
        for word in words:
            if word in self.lexicon or '*' in word:
                corrected_words.append(word)
            else:
                suggestions = self.get_suggestions(word)
                if suggestions:
                    corrected_words.append(suggestions[0])
                else:
                    corrected_words.append(word)
                    
        return ' '.join(corrected_words) 
    