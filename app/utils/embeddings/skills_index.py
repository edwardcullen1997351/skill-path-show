"""
Skills Index for Semantic Matching.

This module manages the pre-computed skill embeddings
and provides methods for building and querying the index.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple

from app.utils.embeddings.model import get_embedding_model, is_embedding_available
from app.utils.embeddings.vector_store import get_vector_store, is_vector_store_available


def get_data_path(filename: str) -> str:
    """Get path to data file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", filename)


class SkillsIndex:
    """
    Skills index using embeddings and vector store.
    
    Manages pre-computed embeddings for all skills in the taxonomy
    for fast semantic similarity search.
    """
    
    def __init__(self):
        """Initialize the skills index."""
        self._embedding_model = None
        self._vector_store = None
        self._skills_data: Dict[str, Dict] = {}
    
    @property
    def embedding_model(self):
        """Get the embedding model (lazy loaded)."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model
    
    @property
    def vector_store(self):
        """Get the vector store (lazy loaded)."""
        if self._vector_store is None:
            self._vector_store = get_vector_store()
        return self._vector_store
    
    def is_available(self) -> bool:
        """
        Check if skills index is available.
        
        Returns:
            True if both embedding model and vector store work
        """
        return is_embedding_available() and is_vector_store_available()
    
    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load skills taxonomy from data file."""
        taxonomy_path = get_data_path("skills_taxonomy.json")
        
        try:
            with open(taxonomy_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _extract_skill_variants(self, taxonomy: Dict) -> Dict[str, List[str]]:
        """
        Extract all skill variants from taxonomy.
        
        Args:
            taxonomy: Skills taxonomy dictionary
            
        Returns:
            Dict mapping skill_id to list of variant names
        """
        skill_variants = {}
        
        for category, skills in taxonomy.items():
            for skill_id, variants in skills.items():
                if isinstance(variants, list):
                    all_variants = [skill_id] + variants
                else:
                    all_variants = [skill_id]
                skill_variants[skill_id] = all_variants
        
        return skill_variants
    
    def build_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build the skills index with embeddings.
        
        Args:
            force_rebuild: Whether to rebuild even if exists
            
        Returns:
            Dict with build statistics
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Embedding model or vector store not available",
                "skills_indexed": 0
            }
        
        current_count = self.vector_store.count()
        if current_count > 0 and not force_rebuild:
            return {
                "success": True,
                "message": f"Index already exists with {current_count} skills",
                "skills_indexed": current_count,
                "rebuilt": False
            }
        
        taxonomy = self._load_taxonomy()
        if not taxonomy:
            return {
                "success": False,
                "error": "Could not load skills taxonomy",
                "skills_indexed": 0
            }
        
        skill_variants = self._extract_skill_variants(taxonomy)
        
        all_skills = list(skill_variants.keys())
        all_variants = []
        skill_ids = []
        metadatas = []
        
        for skill_id, variants in skill_variants.items():
            for variant in variants:
                all_variants.append(variant)
                skill_ids.append(skill_id)
                metadatas.append({
                    "skill_id": skill_id,
                    "variant": variant,
                    "category": "unknown"
                })
                
                for category, skills in taxonomy.items():
                    if skill_id in skills:
                        metadatas[-1]["category"] = category
                        break
        
        if not all_variants:
            return {
                "success": False,
                "error": "No skills to index",
                "skills_indexed": 0
            }
        
        embeddings = self.embedding_model.encode_skills(all_variants)
        if embeddings is None:
            return {
                "success": False,
                "error": "Failed to generate embeddings",
                "skills_indexed": 0
            }
        
        ids = [f"skill_{i}" for i in range(len(all_variants))]
        
        success = self.vector_store.add_embeddings(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=all_variants
        )
        
        if success:
            unique_skills = len(all_skills)
            total_variants = len(all_variants)
            return {
                "success": True,
                "skills_indexed": unique_skills,
                "variants_indexed": total_variants,
                "rebuilt": force_rebuild
            }
        else:
            return {
                "success": False,
                "error": "Failed to store embeddings",
                "skills_indexed": 0
            }
    
    def find_similar_skills(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find similar skills using semantic embeddings.
        
        Args:
            query: Skill name to search for
            top_k: Number of results to return
            threshold: Minimum similarity score
            
        Returns:
            List of matching skills with scores
        """
        if not self.is_available():
            return []
        
        query_embedding = self.embedding_model.encode(query)
        if query_embedding is None:
            return []
        
        ids, distances, metadatas = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k * 2
        )
        
        results = []
        seen_skills = set()
        
        for i, skill_id in enumerate(ids):
            if skill_id in seen_skills:
                continue
            
            score = 1.0 - distances[i] if i < len(distances) else 0
            
            if score < threshold:
                continue
            
            results.append({
                "skill_id": metadatas[i].get("skill_id", skill_id) if i < len(metadatas) else skill_id,
                "matched_variant": metadatas[i].get("variant", "") if i < len(metadatas) else "",
                "score": round(score, 4),
                "method": "semantic"
            })
            
            seen_skills.add(metadatas[i].get("skill_id", skill_id) if i < len(metadatas) else skill_id)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_skill_variants(self, skill_id: str) -> List[str]:
        """
        Get all variants of a skill.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of variant names
        """
        taxonomy = self._load_taxonomy()
        
        for category, skills in taxonomy.items():
            if skill_id in skills:
                variants = skills[skill_id]
                if isinstance(variants, list):
                    return [skill_id] + variants
                return [skill_id]
        
        return []
    
    def get_all_skills(self) -> List[str]:
        """
        Get all unique skill IDs.
        
        Returns:
            List of skill IDs
        """
        taxonomy = self._load_taxonomy()
        
        all_skills = []
        for category, skills in taxonomy.items():
            all_skills.extend(skills.keys())
        
        return sorted(set(all_skills))
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dict with index stats
        """
        taxonomy = self._load_taxonomy()
        
        unique_skills = 0
        total_variants = 0
        for skills in taxonomy.values():
            unique_skills += len(skills)
            for variants in skills.values():
                if isinstance(variants, list):
                    total_variants += len(variants)
                else:
                    total_variants += 1
        
        indexed = self.vector_store.count() if self.is_available() else 0
        
        return {
            "taxonomy_skills": unique_skills,
            "taxonomy_variants": total_variants,
            "indexed_embeddings": indexed,
            "embedding_model": self.embedding_model.model_name if self.is_available() else None,
            "vector_store_available": self.is_available()
        }


_index: Optional[SkillsIndex] = None


def get_skills_index() -> SkillsIndex:
    """
    Get the global skills index instance.
    
    Returns:
        SkillsIndex instance
    """
    global _index
    if _index is None:
        _index = SkillsIndex()
    return _index


def rebuild_skills_index(force: bool = False) -> Dict[str, Any]:
    """
    Rebuild the skills index.
    
    Args:
        force: Whether to force rebuild
        
    Returns:
        Build result statistics
    """
    index = get_skills_index()
    return index.build_index(force_rebuild=force)