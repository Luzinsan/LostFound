import numpy as np
import heapq

class BallTreeNode:
    def __init__(self, indices, pivot, radius, left=None, right=None):
        self.indices = indices  # Индексы точек в данном узле
        self.pivot = pivot      # Центр шара (нормированный вектор)
        self.radius = radius    # Радиус шара
        self.left = left        # Левый потомок
        self.right = right      # Правый потомок

class BallTree:
    def __init__(self, data, leaf_size=20):
        self.data = data
        self.leaf_size = leaf_size
        self.root = self._build_tree(np.arange(len(data)))

    def _build_tree(self, indices):
        if len(indices) <= self.leaf_size:
            return BallTreeNode(indices, None, None)

        # Выбираем случайный индекс как начальный центр
        pivot_idx = np.random.choice(indices)
        pivot = self.data[pivot_idx]

        # Находим самую удаленную точку от pivot
        distances = np.linalg.norm(self.data[indices] - pivot, axis=1)
        farthest_idx = indices[np.argmax(distances)]
        farthest_point = self.data[farthest_idx]

        # Разделяем точки на две группы
        left_indices = []
        right_indices = []
        for idx in indices:
            d_pivot = np.linalg.norm(self.data[idx] - pivot)
            d_farthest = np.linalg.norm(self.data[idx] - farthest_point)
            if d_pivot < d_farthest:
                left_indices.append(idx)
            else:
                right_indices.append(idx)

        # Рекурсивно строим поддеревья
        left = self._build_tree(left_indices)
        right = self._build_tree(right_indices)

        # Вычисляем радиус как максимальное расстояние от центра до точек
        radius = np.max(np.linalg.norm(self.data[indices] - pivot, axis=1))

        return BallTreeNode(indices, pivot, radius, left, right)

class SimilaritySearchEngine:
    def __init__(self, id_embedding_dict: dict):
        self.item_ids = list(id_embedding_dict.keys())
        embeddings = np.array(list(id_embedding_dict.values()))
        
        # Нормируем векторы
        self.norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.normalized_embeddings = embeddings / np.where(self.norms == 0, 1e-10, self.norms)
        
        # Строим Ball Tree
        self.tree = BallTree(self.normalized_embeddings)

    def _search_tree(self, query, node, best):
        # Если узел - лист, проверяем все точки
        if node.left is None:
            for idx in node.indices:
                sim = np.dot(self.normalized_embeddings[idx], query)
                if sim > best[0][0]:
                    heapq.heappushpop(best, (sim, idx))
            return

        # Вычисляем расстояние до центра шара
        dist_to_pivot = np.linalg.norm(query - node.pivot)

        # Применяем правило отсечения
        if dist_to_pivot - node.radius > -best[0][0]:
            return

        # Рекурсивный поиск в поддеревьях
        self._search_tree(query, node.left, best)
        self._search_tree(query, node.right, best)

    def find_similar(self, query_embedding: np.ndarray, top_k: int = 5) -> dict:
        # Нормируем запрос
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        
        # Инициализируем кучу для top-k
        best = [(-np.inf, None)] * top_k
        heapq.heapify(best)
        
        # Поиск в дереве
        self._search_tree(query_norm, self.tree.root, best)
        
        # Собираем результаты
        results = {}
        while best:
            sim, idx = heapq.heappop(best)
            if idx is not None:
                results[self.item_ids[idx]] = float(-sim)
        
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True)[:top_k])



# items = {
#         "item1": np.random.randn(128),
#         "item2": np.random.randn(128),
#         "item3": np.random.randn(128),
#         "item4": np.random.randn(128),
#         "item5": np.random.randn(128),
# }
    

# search_engine = SimilaritySearchEngine(items)
# query = np.random.randn(128)
# results = search_engine.find_similar(query, top_k=3)
# print("Top Similar Items:")
# for item_id, similarity in results.items():
#     print(f"{item_id}: {similarity:.3f}")
