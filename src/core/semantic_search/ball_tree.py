from typing import Optional
import numpy as np
import heapq
import logging
import sys, os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from src.utils.mongodb_handler import mongo_manager


class BallTreeNode:
    def __init__(self, indices, pivot, radius, left=None, right=None):
        """
        Initialize a node in the ball tree.
        
        Args:
            indices: Indices of points in this node
            pivot: Ball center (normalized vector)
            radius: Ball radius
            left: Left child node
            right: Right child node
        """
        try:
            self.indices = indices  # Point indices in this node
            self.pivot = pivot      # Ball center (normalized vector)
            self.radius = radius    # Ball radius
            self.left = left        # Left child
            self.right = right      # Right child
        except Exception as e:
            logging.error(f"Error initializing BallTreeNode: {e} - Failed to create a new node in the ball tree structure")
            raise

    def to_dict(self):
        """Convert node to dictionary for MongoDB storage"""
        try:
            node_dict = {
                'indices': mongo_manager.convert_to_float(self.indices),
                'radius': mongo_manager.convert_to_float(self.radius)
            }
            
            if self.pivot is not None:
                node_dict['pivot'] = mongo_manager.convert_to_float(self.pivot)
                
            if self.left is not None:
                node_dict['left'] = self.left.to_dict()
                
            if self.right is not None:
                node_dict['right'] = self.right.to_dict()
                
            return node_dict
        except Exception as e:
            logging.error(f"Error converting BallTreeNode to dictionary: {e} - Failed to serialize node data for MongoDB storage")
            raise

    @classmethod
    def from_dict(cls, node_dict):
        """Create node from dictionary stored in MongoDB"""
        try:
            indices = np.array(node_dict['indices'])
            pivot = np.array(node_dict['pivot']) if 'pivot' in node_dict else None
            radius = node_dict['radius']
            
            left = cls.from_dict(node_dict['left']) if 'left' in node_dict else None
            right = cls.from_dict(node_dict['right']) if 'right' in node_dict else None
            
            return cls(indices, pivot, radius, left, right)
        except Exception as e:
            logging.error(f"Error creating BallTreeNode from dictionary: {e} - Failed to deserialize node data from MongoDB")
            raise

class BallTree:
    def __init__(self, data, leaf_size=20):
        try:
            self.data = data
            self.leaf_size = leaf_size
            self.root = self._build_tree(np.arange(len(data)))
        except Exception as e:
            logging.error(f"Error initializing BallTree: {e} - Failed to create the ball tree structure")
            raise

    def _build_tree(self, indices):
        """
        Build a ball tree recursively.
        
        Args:
            indices: Indices of points to include in this subtree
        """
        try:
            if len(indices) <= self.leaf_size:
                return BallTreeNode(indices, None, None)

            # Choose a random index as initial center
            pivot_idx = np.random.choice(indices)
            pivot = self.data[pivot_idx]

            # Find the point furthest from pivot
            distances = np.linalg.norm(self.data[indices] - pivot, axis=1)
            farthest_idx = indices[np.argmax(distances)]
            farthest_point = self.data[farthest_idx]

            # Split points into two groups
            left_indices = []
            right_indices = []
            for idx in indices:
                d_pivot = np.linalg.norm(self.data[idx] - pivot)
                d_farthest = np.linalg.norm(self.data[idx] - farthest_point)
                if d_pivot < d_farthest:
                    left_indices.append(idx)
                else:
                    right_indices.append(idx)

            # Recursively build subtrees
            left = self._build_tree(left_indices)
            right = self._build_tree(right_indices)

            # Calculate radius as maximum distance from center to points
            radius = np.max(np.linalg.norm(self.data[indices] - pivot, axis=1))

            return BallTreeNode(indices, pivot, radius, left, right)
        except Exception as e:
            logging.error(f"Error building ball tree node: {e} - Failed to construct a node in the ball tree hierarchy")
            raise

    def to_dict(self):
        """Convert tree to dictionary for MongoDB storage"""
        try:
            return self.root.to_dict()
        except Exception as e:
            logging.error(f"Error converting ball tree to dictionary: {e} - Failed to serialize the entire ball tree structure")
            raise

    @classmethod
    def from_dict(cls, tree_dict, data):
        """Create tree from dictionary stored in MongoDB"""
        try:
            tree = cls(data, leaf_size=20)
            tree.root = BallTreeNode.from_dict(tree_dict)
            return tree
        except Exception as e:
            logging.error(f"Error creating ball tree from dictionary: {e} - Failed to reconstruct the ball tree from stored data")
            raise

class SimilaritySearchEngine:
    def __init__(self, id_embedding_dict: dict, city: Optional[str] = None):
        try:
            self.item_ids = list(id_embedding_dict.keys())
            embeddings = np.array(list(id_embedding_dict.values()))
            
            # Normalize vectors
            self.norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            self.normalized_embeddings = embeddings / np.where(self.norms == 0, 1e-10, self.norms)
            
            # Build Ball Tree
            self.tree = BallTree(self.normalized_embeddings)
            
            if city:
                self._save_tree_to_mongodb(city)
        except Exception as e:
            logging.error(f"Error initializing SimilaritySearchEngine: {e} - Failed to initialize the semantic search engine")
            raise

    def _save_tree_to_mongodb(self, city: str):
        """Save the ball tree to MongoDB for the specified city"""
        try:
            # Get city document
            city_data = mongo_manager.load({"city": city}, "cities")
            if not city_data or len(city_data) == 0:
                logging.error(f"No city data found for: {city}")
                return
            
            # Convert tree to dictionary format
            tree_dict = self.tree.to_dict()
            
            # Update city document with tree data
            city_doc = city_data[0]
            city_doc['ball_tree'] = {
                'tree': tree_dict,
                'item_ids': self.item_ids,
                'normalized_embeddings': mongo_manager.convert_to_float(self.normalized_embeddings),
                'norms': mongo_manager.convert_to_float(self.norms)
            }
            
            # Save updated document
            mongo_manager.save(city_doc, "cities")
            logging.info(f"Ball tree saved to MongoDB for city: {city}")
            
        except Exception as e:
            logging.error(f"Error saving ball tree to MongoDB for city {city}: {e} - Failed to persist the ball tree structure in the database")
            raise

    @classmethod
    def from_mongodb(cls, city: str):
        """Create search engine from MongoDB data for the specified city"""
        try:
            # Get city data with ball tree
            city_data = mongo_manager.load({"city": city}, "cities")
            if not city_data or len(city_data) == 0 or 'ball_tree' not in city_data[0]:
                logging.error(f"No ball tree found for city: {city}")
                return None
            
            # Get ball tree data
            ball_tree_data = city_data[0]['ball_tree']
            
            # Create embeddings dictionary
            id_embedding_dict = {
                item_id: np.array(embedding)
                for item_id, embedding in zip(ball_tree_data['item_ids'], ball_tree_data['normalized_embeddings'])
            }
            
            # Create search engine
            engine = cls(id_embedding_dict)
            
            # Reconstruct tree from stored data
            engine.tree = BallTree.from_dict(ball_tree_data['tree'], engine.normalized_embeddings)
            
            return engine
            
        except Exception as e:
            logging.error(f"Error creating search engine from MongoDB for city {city}: {e} - Failed to load and reconstruct the search engine from database")
            raise

    def _search_tree(self, query, node, best):
        """
        Search the ball tree for nearest neighbors.
        
        Args:
            query: Query point
            node: Current node in the tree
            best: Current best results
        """
        try:
            # If node is leaf, check all points
            if node.left is None:
                for idx in node.indices:
                    sim = np.dot(self.normalized_embeddings[idx], query)
                    if sim > best[0][0]:
                        heapq.heappushpop(best, (sim, idx))
                return

            # Calculate distance to ball center
            dist_to_pivot = np.linalg.norm(query - node.pivot)

            # Apply pruning rule
            if dist_to_pivot - node.radius > -best[0][0]:
                return

            # Recursive search in subtrees
            self._search_tree(query, node.left, best)
            self._search_tree(query, node.right, best)
        except Exception as e:
            logging.error(f"Error searching in ball tree: {e} - Failed to traverse the ball tree during similarity search")
            raise

    def find_similar(self, query_embedding: np.ndarray, top_k: int = 5) -> dict:
        """
        Find similar items using ball tree search.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
        """
        try:
            # Normalize query
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            
            # Initialize heap for top-k
            best = [(-np.inf, None)] * top_k
            heapq.heapify(best)
            
            # Search in tree
            self._search_tree(query_norm, self.tree.root, best)
            
            # Collect results
            results = {}
            while best:
                sim, idx = heapq.heappop(best)
                if idx is not None:
                    results[self.item_ids[idx]] = float(sim)
            
            return dict(sorted(results.items(), key=lambda x: x[1], reverse=True)[:top_k])
        except Exception as e:
            logging.error(f"Error finding similar items: {e} - Failed to find similar items using the ball tree search")
            raise
        