"""
Selected Technique: Pre-trained Sentence-BERT (SBERT) model, specifically all-MiniLM-L6-v2.
This model generates 384-dimensional embeddings, balancing speed and accuracy.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union

class SBERTEmbeddingPipeline:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', 
                 save_path: str = 'embeddings/embeddings.npy'):
        self.model_name = model_name
        self.save_path = save_path
        self.model = None
        self.embeddings = None
        
    def initialize_model(self):
        """Загрузка предобученной модели"""
        self.model = SentenceTransformer(self.model_name)
        
    def load_data(self, file_path: str) -> List[str]:

        #Загрузка текстовых данных из файла
    
        with open(file_path, 'r', encoding='utf-8') as f:
            documents = [line.strip() for line in f if line.strip()]
        return documents
    
    def generate_embeddings(self, texts: List[str], 
                           convert_to_numpy: bool = True) -> Union[np.ndarray, list]:

        #Генерация эмбеддингов для списка текстов

        if not self.model:
            self.initialize_model()
            
        self.embeddings = self.model.encode(
            texts, 
            convert_to_tensor=True, 
            show_progress_bar=True
        )
        
        if convert_to_numpy:
            self.embeddings = self.embeddings.cpu().numpy()
            
        return self.embeddings
    
    def save_embeddings(self):
        #Сохранение эмбеддингов в файл
        if self.embeddings is not None:
            np.save(self.save_path, self.embeddings)
        else:
            raise ValueError("Embeddings not generated yet!")
    
    def load_embeddings(self) -> np.ndarray:
        #Загрузка ранее сохраненных эмбеддингов
        self.embeddings = np.load(self.save_path)
        return self.embeddings

"""
# Пример использования
    
pipeline = SBERTEmbeddingPipeline()
documents = pipeline.load_data('embeddings/test_file.txt')
embeddings = pipeline.generate_embeddings(documents)
pipeline.save_embeddings()
print(f"Generated embeddings shape: {embeddings.shape}")
print(f"Sample embedding: {embeddings[0][:10]}...")
"""
