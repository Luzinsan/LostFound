from collections import defaultdict
#with Edit Distance and N-gram Overlap
class SpellChecker:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.gram_index = defaultdict(set)
        self.n = 2  
        
        
        for term in lexicon:
            padded = f"${term}$"
            for i in range(len(padded) - self.n + 1):
                gram = padded[i:i+self.n]
                self.gram_index[gram].add(term)
    
    def _edit_distance(self, s1, s2):
        m, n = len(s1), len(s2)
        dp = [[0]*(n+1) for _ in range(m+1)]
        for i in range(m+1):
            for j in range(n+1):
                if i == 0:
                    dp[i][j] = j
                elif j == 0:
                    dp[i][j] = i
                else:
                    cost = 0 if s1[i-1] == s2[j-1] else 1
                    dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
        return dp[m][n]
    
    def _get_candidates(self, term, threshold=0.5):
        padded = f"${term}$"
        term_grams = {padded[i:i+self.n] for i in range(len(padded) - self.n + 1)}
        candidates = defaultdict(int)
        for gram in term_grams:
            for word in self.gram_index.get(gram, set()):
                candidates[word] += 1

        max_overlap = len(term_grams)
        return [word for word, count in candidates.items() 
                if count / (len(term_grams) + len(self.gram_index[gram]) - count) > threshold]
    
    def correct(self, term, max_distance=2):
        if term in self.lexicon:
            return [term]
        candidates = self._get_candidates(term)
        scored = [(word, self._edit_distance(term, word)) for word in candidates]
        return [word for word, dist in sorted(scored, key=lambda x: x[1]) if dist <= max_distance]
