**Why Ball Tree?**  
- Supports **cosine distance**.  
- Efficient for **high-dimensional data** (e.g., BERT embeddings).  
- Integrates easily with `scikit-learn`.  

- **Metric**: Cosine distance aligns with semantic similarity.  
- **Scalability**: Handles 10k+ items with sub-second query times.  
- **Dimensionality**: Optimized for high-dimensional spaces (BERT’s 768D).  

**Comparison to Alternatives**:  
| Method      | Pros                          | Cons                          |  
|-------------|-------------------------------|-------------------------------|  
| **Ball Tree** | Fast for cosine similarity    | Higher memory usage           |  
| **VP Tree**  | Memory-efficient              | Slower for high dimensions    |  
| **KD Tree**  | Fast for low dimensions       | Fails in high-dimensionality  |  

**Ball Tree** for **cosine similarity search** to efficiently find the top-k most similar items to a query embedding.  

1. **Initialization:**  
   - Embeddings are normalized (L2-normalized) to enable cosine similarity via dot products.  
   - A hierarchical **Ball Tree** is built, where each node:  
     - Represents a subset of data points (`indices`).  
     - Stores a `pivot` (center of the ball) and `radius` (max distance from pivot to any point in the node).  
     - Recursively splits data into left/right subtrees based on proximity to pivot points.  

2. **Search Process:**  
   - The query is normalized.  
   - The tree is traversed recursively, **pruning branches** using the triangle inequality:  
     *If the minimum possible distance from the query to the node’s ball is worse than the current best matches, skip the subtree.*  
   - A **priority queue (heap)** dynamically tracks the top-k matches for efficiency.  

**Why It’s Efficient:**  
- Avoids brute-force search by leveraging the tree structure to prune irrelevant branches.  
- Uses **heapq** to maintain top-k results in `O(log k)` time per update.  

**Key Takeaway:**  
This Ball Tree implementation reduces search complexity from `O(N)` (brute-force) to roughly `O(log N)` in practice, ideal for large datasets.
