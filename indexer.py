import torch
from PIL import Image
import os
from transformers import AutoProcessor, AutoModel
import numpy as np
import faiss
import pickle
import time

class IndexerResult:
    index : int
    score : float

    def __init__(self, index, score):
        self.index = index
        self.score = score

class Indexer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load CLIP model
        self.model = AutoModel.from_pretrained("google/siglip-so400m-patch14-384").to(self.device)
        self.processor = AutoProcessor.from_pretrained("google/siglip-so400m-patch14-384")
        
        # Initialize FAISS index
        self.dimension = 1152 # SigLIP embedding dimension
        # self.dimension = self.model.projection_dim # CLIP embedding dimension
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
    
    def add_embeddings(self, embeddings) -> int:
        """ Add embeddings to FAISS index"""
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        return self.index.ntotal - 1
    
    def encode_text(self, text):
        """Encode text query using CLIP"""
        inputs = self.processor(text=text, return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            text_embeddings = text_features.cpu().numpy()
        
        # Normalize embeddings
        text_embeddings = text_embeddings / np.linalg.norm(text_embeddings, axis=1, keepdims=True)
        
        return text_embeddings
    
    def search(self, query : str, k=8) -> list[IndexerResult]:
        """Search for similar images using text query"""
        text_embedding = self.encode_text(query)
        scores, indices = self.index.search(text_embedding.astype('float32'), k)
        
        results = []
        for idx, score in zip(indices[0], scores[0]):
            results.append(IndexerResult(idx, score))
        
        return results
    
    def encode_query_image(self, image : Image):
        """Encode query image using CLIP"""
        image = image.convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            image_embeddings = image_features.cpu().numpy()
        
        # Normalize embeddings
        image_embeddings = image_embeddings / np.linalg.norm(image_embeddings, axis=1, keepdims=True)
        
        return image_embeddings
    
    def search_by_image(self, image : Image, k=8) -> list[IndexerResult]:
        """Search for similar images using an image query"""
        image_embedding = self.encode_query_image(image)
        scores, indices = self.index.search(image_embedding.astype('float32'), k)
        
        results = []
        for idx, score in zip(indices[0], scores[0]):
            results.append(IndexerResult(int(idx), float(score)))
        return results
    
    def save_index(self, filename="images.index"):
        """Save the index to a file"""
        faiss.write_index(self.index, filename)
    
    def load_index(self, filename="images.index"):
        """Load the index from a file"""
        self.index = faiss.read_index(filename)