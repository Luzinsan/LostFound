from transformers import AutoTokenizer, AutoModel
import torch
import re
import requests
from urllib.parse import quote

class RussianBERTEmbedder:
    def __init__(self, model_name='cointegrated/rubert-tiny2', device=None, translate_en=False):
        self.translate_en = translate_en
        self.device = device or 'cpu'
        
        # Инициализация русской модели
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        # Настройки для lowercasing
        self.do_lower_case = getattr(self.tokenizer, 'do_lower_case', False)

    def _translate_text(self, text):
        """Простой перевод через LibreTranslate API"""
        try:
            encoded_text = quote(text)
            url = f"https://libretranslate.com/translate"
            data = {
                'q': text,
                'source': 'en',
                'target': 'ru',
                'format': 'text'
            }
            response = requests.post(url, json=data)
            return response.json()['translatedText']
        except Exception as e:
            raise RuntimeError(f"Translation error: {str(e)}")

    def _preprocess(self, text):
        text = re.sub(r'\s+', ' ', text).strip().replace("ё", "е")
        return text.lower() if self.do_lower_case else text

    def text_to_embedding(self, texts, pooling='mean', normalize=False):
        is_single = isinstance(texts, str)
        texts = [texts] if is_single else texts
        
        if self.translate_en:
            texts = [self._translate_text(t) if self._has_english(t) else t for t in texts]
        
        processed = [self._preprocess(t) for t in texts]
        
        inputs = self.tokenizer(
            processed,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=312
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        if pooling == 'mean':
            mask = inputs['attention_mask'].unsqueeze(-1)
            embeddings = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        elif pooling == 'cls':
            embeddings = outputs.last_hidden_state[:, 0, :]
        else:
            raise ValueError("Invalid pooling method")
            
        if normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
        return embeddings.cpu().numpy()[0] if is_single else embeddings.cpu().numpy()

    def _has_english(self, text):
        return bool(re.search('[a-zA-Z]', text))




# Пример вызова         
# embedder = RussianBERTEmbedder()
# text = "Hello world! Это пример текста на русском языке."
# embedding = embedder.text_to_embedding(text)
# print(embedding)
