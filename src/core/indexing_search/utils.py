import numpy as np
from typing import List, Dict, Any

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def combine_scores(tfidf_score: float, embedding_score: float, 
                  tfidf_weight: float = 0.3, embedding_weight: float = 0.7) -> float:
    """
    Combine TF-IDF and embedding similarity scores using weighted average.
    
    Args:
        tfidf_score: TF-IDF score (0-1)
        embedding_score: Embedding similarity score (0-1)
        tfidf_weight: Weight for TF-IDF score (default: 0.3)
        embedding_weight: Weight for embedding score (default: 0.7)
        
    Returns:
        Combined score between 0 and 1
    """
    return (tfidf_score * tfidf_weight) + (embedding_score * embedding_weight)

def normalize_scores(scores: List[float]) -> List[float]:
    """
    Normalize scores to range [0, 1] using min-max normalization.
    
    Args:
        scores: List of scores to normalize
        
    Returns:
        List of normalized scores
    """
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0] * len(scores)
        
    return [(score - min_score) / (max_score - min_score) for score in scores] 