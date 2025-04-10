from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import re

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
        self.model.eval()
        
    def _preprocess(self, text):
        """Basic normalization for text"""
        return re.sub(r'\s+|\n+|\t+', ' ', text).strip().replace("ё", "е").lower()

    def text_to_embedding(self, text, pooling='mean'):
        """
        Generate embedding using selected pooling strategy:
        - 'mean': average all token embeddings
        - 'cls': use [CLS] token embedding
        """
        text = self._preprocess(text)
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=312
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        if pooling == 'mean':
            return torch.mean(outputs.last_hidden_state[0], dim=0).numpy()
        elif pooling == 'cls':
            return outputs.last_hidden_state[0][0].numpy()
        else:
            raise ValueError("Invalid pooling method")
