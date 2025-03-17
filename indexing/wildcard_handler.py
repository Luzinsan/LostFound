import re
from collections import defaultdict
from typing import  List


class WildcardHandler:
    def __init__(self, corpus):
        self.k = 3
        self.forward_index = defaultdict(set)
        self.reverse_index = defaultdict(set)
        self.lexicon = set(corpus)
        
        # Build forward and reverse k-gram indexes
        for term in corpus:
            padded = f"${term}$"
            for i in range(len(padded) - self.k + 1):
                gram = padded[i:i+self.k]
                self.forward_index[gram].add(term)
            
            reversed_term = term[::-1]
            padded_rev = f"${reversed_term}$"
            for i in range(len(padded_rev) - self.k + 1):
                gram = padded_rev[i:i+self.k]
                self.reverse_index[gram].add(term)

    def process_query(self, query: str) -> List[str]:
        """Обработка wildcard-запросов с использованием k-gram индекса"""
        parts = query.split('*')
        
        # Обработка различных типов wildcard-запросов
        if query.startswith('*'):
            reversed_part = parts[-1][::-1]
            grams = [f"${reversed_part}$"]
            candidates = self.reverse_index.get(grams[0], set())
        elif query.endswith('*'):
            grams = [f"${parts[0]}"]
            candidates = self.forward_index.get(grams[0], set())
        else:
            prefix = f"${parts[0]}"
            suffix = f"{parts[-1]}$"
            prefix_grams = self.forward_index.get(prefix, set())
            suffix_grams = self.forward_index.get(suffix, set())
            candidates = prefix_grams & suffix_grams
        
        # Фильтрация с использованием регулярных выражений
        pattern = query.replace('*', '.*')
        regex = re.compile(f'^{pattern}$')
        return [term for term in candidates if regex.match(term)]
