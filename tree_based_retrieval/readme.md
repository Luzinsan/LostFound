**Why Ball Tree?**  
- Supports **cosine distance** (ideal for semantic similarity).  
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
