# Install required packages
# !pip install transformers torch sentencepiece

from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

class RussianBERTEmbedder:
    def __init__(self, model_name='cointegrated/rubert-tiny2'):
        """
        Initialize Russian BERT model
        Options: 
        - 'cointegrated/rubert-tiny2' (lightweight)
        - 'DeepPavlov/rubert-base-cased' (full)
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()  # disable dropout
        
    def _russian_preprocess(self, text):
        """Basic normalization for Russian text"""
        return text.lower().replace("ё", "е")  # handle ё/е variation

    def text_to_embedding(self, text, pooling='mean'):
        """
        Generate embedding using selected pooling strategy:
        - 'mean': average all token embeddings
        - 'cls': use [CLS] token embedding
        """
        text = self._russian_preprocess(text)
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        if pooling == 'mean':
            return torch.mean(outputs.last_hidden_state[0], dim=0).numpy()
        elif pooling == 'cls':
            return outputs.last_hidden_state[0][0].numpy()
        else:
            raise ValueError("Invalid pooling method")

    def generate_embeddings_from_file(self, input_path, output_path, pooling='mean'):
        """Process text file line by line"""
        with open(input_path, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f]
            embeddings = [self.text_to_embedding(text, pooling) for text in texts]

        # Save to file
        if output_path.endswith('.npy'):
            np.save(output_path, np.array(embeddings))
        elif output_path.endswith('.txt'):
            with open(output_path, 'w', encoding='utf-8') as f:
                for emb in embeddings:
                    f.write(','.join(map(str, emb)) + '\n')
        else:
            raise ValueError("Unsupported file format. Use .npy or .txt")

        return embeddings

"""
#Примеры использования
embedder = RussianBERTEmbedder()
    
    # Single text embedding
sample_text = "Чисто для теста"
embedding = embedder.text_to_embedding(sample_text)
print(f"Embedding shape: {embedding.shape}")
print(f"Sample values: {embedding[:5]}...")
    
    # File processing
file_embeddings = embedder.generate_embeddings_from_file('embeddings/test_file.txt', 'embeddings/embeddings.txt')
print(f"Generated {len(file_embeddings)} document embeddings")

"""



# """
# Selected Technique: Pre-trained Sentence-BERT (SBERT) model, specifically all-MiniLM-L6-v2.
# This model generates 384-dimensional embeddings, balancing speed and accuracy.
# """

# import numpy as np
# from sentence_transformers import SentenceTransformer
# from typing import List, Union

# class SBERTEmbeddingPipeline:
#     def __init__(self, model_name: str = 'all-MiniLM-L6-v2', 
#                  save_path: str = 'embeddings/embeddings.npy'):
#         self.model_name = model_name
#         self.save_path = save_path
#         self.model = None
#         self.embeddings = None
        
#     def initialize_model(self):
#         """Загрузка предобученной модели"""
#         self.model = SentenceTransformer(self.model_name)
        
#     def load_data(self, file_path: str) -> List[str]:

#         #Загрузка текстовых данных из файла
    
#         with open(file_path, 'r', encoding='utf-8') as f:
#             documents = [line.strip() for line in f if line.strip()]
#         return documents
    
#     def generate_embeddings(self, texts: List[str], 
#                            convert_to_numpy: bool = True) -> Union[np.ndarray, list]:

#         #Генерация эмбеддингов для списка текстов

#         if not self.model:
#             self.initialize_model()
            
#         self.embeddings = self.model.encode(
#             texts, 
#             convert_to_tensor=True, 
#             show_progress_bar=True
#         )
        
#         if convert_to_numpy:
#             self.embeddings = self.embeddings.cpu().numpy()
            
#         return self.embeddings
    
#     def save_embeddings(self):
#         #Сохранение эмбеддингов в файл
#         if self.embeddings is not None:
#             np.save(self.save_path, self.embeddings)
#         else:
#             raise ValueError("Embeddings not generated yet!")
    
#     def load_embeddings(self) -> np.ndarray:
#         #Загрузка ранее сохраненных эмбеддингов
#         self.embeddings = np.load(self.save_path)
#         return self.embeddings

# """
# # Пример использования
    
# pipeline = SBERTEmbeddingPipeline()
# documents = pipeline.load_data('embeddings/test_file.txt')
# embeddings = pipeline.generate_embeddings(documents)
# pipeline.save_embeddings()
# print(f"Generated embeddings shape: {embeddings.shape}")
# print(f"Sample embedding: {embeddings[0][:10]}...")
# """
