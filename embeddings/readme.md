### **Full Algorithm Description: Russian BERT Text Embedding Generation**

This algorithm generates dense vector representations (embeddings) for Russian text using a pre-trained BERT model.

---

### **1. Initialization**
**Input:**  
- `model_name`: Pre-trained BERT model identifier (default: `'cointegrated/rubert-tiny2'`).

**Steps:**  
1. **Load Tokenizer and Model**:  
   - Use Hugging Face's `AutoTokenizer` and `AutoModel` to load the specified BERT model and its corresponding tokenizer.  
   - **Example Models**:  
     - Lightweight: `cointegrated/rubert-tiny2` (12-layer, 312-dim embeddings).  
     - Full: `DeepPavlov/rubert-base-cased` (12-layer, 768-dim embeddings).  
   - **Model Configuration**:  
     - The model is set to evaluation mode (`model.eval()`) to disable dropout and gradient computation.  

---

### **2. Text Preprocessing**
**Input:**  
- Raw text string (e.g., `"Привет, как дела?"`).  

**Steps:**  
1. **Normalization**:  
   - Replace multiple whitespaces, newlines, or tabs with a single space.  
   - Convert "ё" to "е" (standard in Russian text processing).  
   - Convert text to lowercase.  
   - **Example**:  
     - Input: `"  Привет,\nкак\tдела?  "`  
     - Output: `"привет, как дела?"`  

---

### **3. Tokenization**
**Input:**  
- Preprocessed text.  

**Steps:**  
1. **Tokenize Text**:  
   - Split text into subword tokens using the BERT tokenizer (e.g., WordPiece).  
   - Add special tokens: `[CLS]` (start) and `[SEP]` (end).  
2. **Padding/Truncation**:  
   - Pad or truncate to a fixed length of 512 tokens (BERT's maximum input size).  
   - **Output Format**:  
     - PyTorch tensor (`return_tensors='pt'`).  

**Example Tokenization**:  
- Text: `"привет, как дела?"`  
- Tokens: `['[CLS]', 'привет', ',', 'как', 'дел', '##а', '?', '[SEP]']`  

---

### **4. Model Inference**
**Input:**  
- Tokenized input tensors.  

**Steps:**  
1. **Forward Pass**:  
   - Pass tokenized input through the BERT model.  
   - Disable gradient computation (`with torch.no_grad()`) for memory efficiency.  
2. **Output Extraction**:  
   - Extract the `last_hidden_state` (token-level embeddings) from the model output.  
   - Shape: `(batch_size, sequence_length, embedding_dim)`  

---

### **5. Pooling Strategy**
**Input:**  
- Token embeddings from `last_hidden_state`.  

**Methods:**  
1. **Mean Pooling** (`pooling='mean'`):  
   - Compute the average of all token embeddings (including padding tokens).  
   - **Formula**:  
     \[
     \text{embedding} = \frac{1}{N} \sum_{i=1}^{N} \text{token}_i
     \]
   - **Limitation**: May include irrelevant padding tokens.  

2. **CLS Pooling** (`pooling='cls'`):  
   - Use the embedding of the `[CLS]` token (first token in the sequence).  
   - Designed for sentence-level classification in BERT.  

---

### **6. Output**
**Result:**  
- A fixed-dimensional numpy array representing the text embedding.  
- **Dimensions**:  
  - `rubert-tiny2`: 312 dimensions.  
  - `rubert-base-cased`: 768 dimensions.  

---

### **Algorithm Workflow Summary**
1. **Input Text** → Preprocess → Tokenize → BERT Model → Pooling → **Embedding**.  
2. **Key Parameters**:  
   - `model_name`: Trade-off between speed (`rubert-tiny2`) and accuracy (`rubert-base-cased`).  
   - `pooling`: Choose based on task (e.g., `mean` for sentence similarity, `cls` for classification).  


### **Applications**
- Semantic search  
- Text classification  
- Clustering  
- Recommendation systems  

### **Limitations**
- Mean pooling includes padding tokens (use attention masks for improvement).  
- Case folding (lowercasing) may lose information for case-sensitive models.  
- Max sequence length of 512 tokens.