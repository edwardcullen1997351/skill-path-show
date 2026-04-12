"""
Embeddings Module for Semantic Skill Matching.

This module provides:
- Embedding model (sentence-transformers)
- Vector store (ChromaDB)
- Skills index for semantic matching
"""

from app.utils.embeddings.model import (
    get_embedding_model,
    is_embedding_available,
    EmbeddingModel
)
from app.utils.embeddings.vector_store import (
    get_vector_store,
    is_vector_store_available,
    VectorStore
)
from app.utils.embeddings.skills_index import (
    get_skills_index,
    rebuild_skills_index,
    SkillsIndex
)


__all__ = [
    "get_embedding_model",
    "is_embedding_available",
    "EmbeddingModel",
    "get_vector_store",
    "is_vector_store_available",
    "VectorStore",
    "get_skills_index",
    "rebuild_skills_index",
    "SkillsIndex"
]