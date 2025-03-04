#use K-grams
from collections import defaultdict
import re

class WildcardHandler:
    def __init__(self, corpus):
        self.k = 3 
        self.forward_index = defaultdict(set)
        self.reverse_index = defaultdict(set)
        self.lexicon = set(corpus)
        
        
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
    
    def _split_wildcard(self, query):
        parts = query.split('*')
        if len(parts) == 1:
            return [query], False
        return parts, True
    
    def process_query(self, query):
        parts, has_wildcard = self._split_wildcard(query)
        if not has_wildcard:
            return [query] if query in self.lexicon else []
        
       
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
            candidates = self.forward_index.get(prefix, set()) & self.forward_index.get(suffix, set())
        
        pattern = query.replace('*', '.*')
        regex = re.compile(f'^{pattern}$')
        return [term for term in candidates if regex.match(term)]
