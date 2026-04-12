"""
Vector Store using ChromaDB.

This module provides persistent vector storage for skill embeddings
using ChromaDB for fast similarity searches.
"""

import os
from typing import List, Optional, Dict, Any, Tuple
import numpy as np


class VectorStore:
    """
    ChromaDB-based vector store for skill embeddings.
    
    Provides methods for:
    - Adding embeddings with metadata
    - Similarity search
    - Collection management
    """
    
    DEFAULT_PERSIST_DIR = "./data/chroma_db"
    COLLECTION_NAME = "skills"
    
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: str = COLLECTION_NAME
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_dir: Directory for persistent storage
            collection_name: Name of the collection
        """
        self._persist_dir = persist_dir or os.getenv(
            "CHROMA_PERSIST_DIR",
            self.DEFAULT_PERSIST_DIR
        )
        self._collection_name = collection_name
        self._client = None
        self._collection = None
        self._initialized = False
    
    def _ensure_dir(self) -> None:
        """Ensure persist directory exists."""
        os.makedirs(self._persist_dir, exist_ok=True)
    
    def _initialize(self) -> bool:
        """
        Initialize ChromaDB client and collection.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        self._ensure_dir()
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"description": "Skill embeddings for semantic matching"}
            )
            
            self._initialized = True
            return True
        except ImportError:
            print("Warning: chromadb not installed")
            return False
        except Exception as e:
            print(f"Warning: Failed to initialize ChromaDB: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if vector store is available.
        
        Returns:
            True if ChromaDB is initialized
        """
        return self._initialize()
    
    def add_embeddings(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None
    ) -> bool:
        """
        Add embeddings to the store.
        
        Args:
            ids: Unique IDs for each embedding
            embeddings: Numpy array of embeddings
            metadatas: Optional metadata for each embedding
            documents: Optional original documents
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            if metadatas is None:
                metadatas = [{} for _ in ids]
            if documents is None:
                documents = ids
            
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=documents
            )
            return True
        except Exception as e:
            print(f"Error adding embeddings: {e}")
            return False
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[float], List[Dict]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Tuple of (ids, distances, metadatas)
        """
        if not self.is_available():
            return [], [], []
        
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )
            
            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            
            return ids, distances, metadatas
        except Exception as e:
            print(f"Error searching embeddings: {e}")
            return [], [], []
    
    def search_by_text(
        self,
        query_text: str,
        embedding_model,
        n_results: int = 5
    ) -> Tuple[List[str], List[float], List[Dict]]:
        """
        Search by text using embedding model.
        
        Args:
            query_text: Query text
            embedding_model: EmbeddingModel instance
            n_results: Number of results
            
        Returns:
            Tuple of (ids, scores, metadatas)
        """
        query_embedding = embedding_model.encode(query_text)
        if query_embedding is None:
            return [], [], []
        
        return self.search(query_embedding, n_results)
    
    def get(self, ids: List[str]) -> Tuple[List[str], List[Dict], List[str]]:
        """
        Get embeddings by IDs.
        
        Args:
            ids: List of IDs to retrieve
            
        Returns:
            Tuple of (ids, metadatas, documents)
        """
        if not self.is_available():
            return [], [], []
        
        try:
            results = self._collection.get(ids=ids)
            return (
                results.get("ids", []),
                results.get("metadatas", []),
                results.get("documents", [])
            )
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            return [], [], []
    
    def delete(self, ids: List[str]) -> bool:
        """
        Delete embeddings by IDs.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            self._collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting embeddings: {e}")
            return False
    
    def count(self) -> int:
        """
        Get the number of embeddings in the store.
        
        Returns:
            Number of embeddings
        """
        if not self.is_available():
            return 0
        return self._collection.count()
    
    def clear(self) -> bool:
        """
        Clear all embeddings from the collection.
        
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            self._client.delete_collection(self._collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"description": "Skill embeddings for semantic matching"}
            )
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
    
    def get_all_skills(self) -> List[str]:
        """
        Get all skill IDs in the store.
        
        Returns:
            List of skill IDs
        """
        if not self.is_available():
            return []
        
        try:
            results = self._collection.get()
            return results.get("ids", [])
        except Exception as e:
            print(f"Error getting all skills: {e}")
            return []


_store: Optional[VectorStore] = None


def get_vector_store(
    persist_dir: Optional[str] = None,
    collection_name: str = "skills"
) -> VectorStore:
    """
    Get the global vector store instance.
    
    Args:
        persist_dir: Optional persist directory override
        collection_name: Collection name
        
    Returns:
        VectorStore instance
    """
    global _store
    if _store is None:
        _store = VectorStore(persist_dir, collection_name)
    return _store


def is_vector_store_available() -> bool:
    """
    Check if vector store is available.
    
    Returns:
        True if ChromaDB is initialized
    """
    store = get_vector_store()
    return store.is_available()