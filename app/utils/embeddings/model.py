"""
Embedding Model Wrapper.

This module provides a wrapper around sentence-transformers
with lazy loading and caching for efficient embedding generation.
"""

import os
from typing import List, Optional, Union
import numpy as np


class EmbeddingModel:
    """
    Wrapper for sentence-transformers model with caching.
    
    Uses all-MiniLM-L6-v2 for fast semantic similarity.
    """
    
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Optional model name override
        """
        self._model_name = model_name or os.getenv("EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self._model = None
        self._loaded = False
    
    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name
    
    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension."""
        return self.EMBEDDING_DIM
    
    def _load_model(self) -> bool:
        """
        Lazy load the sentence-transformer model.
        
        Returns:
            True if successful, False otherwise
        """
        if self._loaded and self._model is not None:
            return True
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._loaded = True
            return True
        except ImportError:
            print("Warning: sentence-transformers not installed")
            return False
        except Exception as e:
            print(f"Warning: Failed to load embedding model: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if the model is available.
        
        Returns:
            True if model can be loaded
        """
        return self._load_model()
    
    def encode(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True,
        show_progress: bool = False
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize embeddings (L2)
            show_progress: Whether to show progress bar
            
        Returns:
            Numpy array of embeddings or None if failed
        """
        if not self._load_model():
            return None
        
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = self._model.encode(
                texts,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return None
    
    def encode_skill(self, skill: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a skill name.
        
        Args:
            skill: Skill name to embed
            
        Returns:
            Embedding vector or None
        """
        return self.encode(skill, normalize=True)
    
    def encode_skills(self, skills: List[str]) -> Optional[np.ndarray]:
        """
        Generate embeddings for multiple skills.
        
        Args:
            skills: List of skill names
            
        Returns:
            Matrix of embeddings (n_skills x 384) or None
        """
        if not skills:
            return None
        return self.encode(skills, normalize=True)
    
    def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> Optional[float]:
        """
        Compute cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1) or None
        """
        embeddings = self.encode([text1, text2])
        if embeddings is None or len(embeddings) < 2:
            return None
        
        from numpy.linalg import norm
        e1, e2 = embeddings[0], embeddings[1]
        
        cos_sim = np.dot(e1, e2) / (norm(e1) * norm(e2))
        return float(cos_sim)
    
    def compute_similarities(
        self,
        query: str,
        candidates: List[str]
    ) -> Optional[List[float]]:
        """
        Compute similarity between query and multiple candidates.
        
        Args:
            query: Query text
            candidates: List of candidate texts
            
        Returns:
            List of similarity scores or None
        """
        if not candidates:
            return None
        
        all_texts = [query] + candidates
        embeddings = self.encode(all_texts)
        
        if embeddings is None:
            return None
        
        from numpy.linalg import norm
        query_emb = embeddings[0]
        query_norm = norm(query_emb)
        
        similarities = []
        for i in range(1, len(embeddings)):
            cand_emb = embeddings[i]
            cos_sim = np.dot(query_emb, cand_emb) / (query_norm * norm(cand_emb))
            similarities.append(float(cos_sim))
        
        return similarities


_model: Optional[EmbeddingModel] = None


def get_embedding_model(model_name: Optional[str] = None) -> EmbeddingModel:
    """
    Get the global embedding model instance.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        EmbeddingModel instance
    """
    global _model
    if _model is None:
        _model = EmbeddingModel(model_name)
    return _model


def is_embedding_available() -> bool:
    """
    Check if embedding model is available.
    
    Returns:
        True if model can be loaded
    """
    model = get_embedding_model()
    return model.is_available()