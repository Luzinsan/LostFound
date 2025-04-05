import numpy as np
from sklearn.neighbors import BallTree

class SimilaritySearchEngine:
    def __init__(self, id_embedding_dict: dict):
        self.item_ids = list(id_embedding_dict.keys())
        embeddings = np.array(list(id_embedding_dict.values()))
        self.norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.normalized_embeddings = embeddings / np.where(self.norms == 0, 1e-10, self.norms)
        self.tree = BallTree(self.normalized_embeddings, metric='euclidean')

    def find_similar(self, query_embedding: np.ndarray, top_k: int = 5) -> dict:
        query_norm = query_embedding / np.linalg.norm(query_embedding)
    
        distances, indices = self.tree.query(query_norm.reshape(1, -1), k=top_k)
        
        # Преобразование расстояния в косинусную близость
        similarities = 1 - (distances[0] ** 2) / 2  # Так как ||u-v||² = 2(1 - cos(u,v))
        
        results = {
            self.item_ids[idx]: float(sim)
            for idx, sim in zip(indices[0], similarities)
        }
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))


#Простой пример
items = {
        "item1": np.random.randn(128),
        "item2": np.random.randn(128),
        "item3": np.random.randn(128),
        "item4": np.random.randn(128),
        "item5": np.random.randn(128),
}
    

search_engine = SimilaritySearchEngine(items)
query = np.random.randn(128)
results = search_engine.find_similar(query, top_k=3)
print("Top Similar Items:")
for item_id, similarity in results.items():
    print(f"{item_id}: {similarity:.3f}")
