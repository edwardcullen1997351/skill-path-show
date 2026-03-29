"""
Cosine similarity module for skill matching.

This module provides embedding-like similarity using cosine similarity
to find similar skills even when they're not exact matches.
"""

import math
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class SkillSimilarity:
    """
    Skill similarity calculator using cosine similarity.
    
    Uses a simple bag-of-words approach to create skill embeddings
    and calculate similarity between skills.
    """
    
    def __init__(self):
        """Initialize the similarity calculator."""
        self._skill_vectors: Dict[str, Dict[str, float]] = {}
        self._initialized = False
    
    def _tokenize_skill(self, skill: str) -> List[str]:
        """
        Tokenize a skill into component words.
        
        Args:
            skill: Skill string
            
        Returns:
            List of tokens
        """
        # Split on common delimiters
        tokens = skill.replace('_', ' ').replace('-', ' ').split()
        return [t.lower() for t in tokens if t]
    
    def _create_skill_vector(self, skill: str) -> Dict[str, float]:
        """
        Create a vector representation of a skill.
        
        Uses character n-grams and word tokens for similarity.
        
        Args:
            skill: Skill string
            
        Returns:
            Dict of feature -> weight
        """
        vector = defaultdict(float)
        
        # Add word tokens
        tokens = self._tokenize_skill(skill)
        for token in tokens:
            vector[f"word_{token}"] = 1.0
        
        # Add character 2-grams for partial matching
        skill_lower = skill.lower()
        for i in range(len(skill_lower) - 1):
            ngram = skill_lower[i:i+2]
            vector[f"ngram_{ngram}"] += 0.5
        
        # Add length feature
        vector["length"] = len(skill_lower)
        
        return dict(vector)
    
    def _build_skill_vectors(self, skills: List[str]) -> None:
        """
        Build vectors for all skills.
        
        Args:
            skills: List of skill strings
        """
        if self._initialized:
            return
        
        for skill in skills:
            if skill not in self._skill_vectors:
                self._skill_vectors[skill] = self._create_skill_vector(skill)
        
        self._initialized = True
    
    def _cosine_similarity(
        self,
        vec1: Dict[str, float],
        vec2: Dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        # Find common keys
        common_keys = set(vec1.keys()) & set(vec2.keys())
        
        if not common_keys:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def find_similar_skills(
        self,
        target_skill: str,
        candidate_skills: List[str],
        threshold: float = 0.3,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find skills similar to the target skill.
        
        Args:
            target_skill: Skill to find matches for
            candidate_skills: List of candidate skills
            threshold: Minimum similarity score (0-1)
            top_k: Maximum number of results
            
        Returns:
            List of (skill, similarity_score) tuples
        """
        # Build vectors
        all_skills = [target_skill] + candidate_skills
        self._build_skill_vectors(all_skills)
        
        # Get target vector
        target_vector = self._skill_vectors.get(
            target_skill,
            self._create_skill_vector(target_skill)
        )
        
        # Calculate similarities
        similarities = []
        
        for skill in candidate_skills:
            if skill == target_skill:
                continue
            
            skill_vector = self._skill_vectors.get(
                skill,
                self._create_skill_vector(skill)
            )
            
            similarity = self._cosine_similarity(target_vector, skill_vector)
            
            if similarity >= threshold:
                similarities.append((skill, similarity))
        
        # Sort by similarity (descending) and take top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_skill_similarity_matrix(
        self,
        skills: List[str]
    ) -> Dict[Tuple[str, str], float]:
        """
        Get pairwise similarity matrix for a list of skills.
        
        Args:
            skills: List of skills
            
        Returns:
            Dict of (skill1, skill2) -> similarity
        """
        self._build_skill_vectors(skills)
        
        matrix = {}
        
        for i, skill1 in enumerate(skills):
            for j, skill2 in enumerate(skills):
                if i >= j:
                    continue
                
                vec1 = self._skill_vectors.get(skill1, {})
                vec2 = self._skill_vectors.get(skill2, {})
                
                similarity = self._cosine_similarity(vec1, vec2)
                
                matrix[(skill1, skill2)] = similarity
                matrix[(skill2, skill1)] = similarity
        
        return matrix
    
    def find_closest_match(
        self,
        query: str,
        options: List[str]
    ) -> Optional[Tuple[str, float]]:
        """
        Find the closest matching skill from a list of options.
        
        Args:
            query: Query string
            options: List of possible matches
            
        Returns:
            Tuple of (best_match, similarity_score) or None
        """
        similar = self.find_similar_skills(
            query,
            options,
            threshold=0.0,  # Return best match regardless
            top_k=1
        )
        
        if similar:
            return similar[0]
        
        return None


# Create a global instance
_skill_similarity: Optional[SkillSimilarity] = None


def get_skill_similarity() -> SkillSimilarity:
    """
    Get the global skill similarity instance.
    
    Returns:
        The singleton SkillSimilarity instance
    """
    global _skill_similarity
    if _skill_similarity is None:
        _skill_similarity = SkillSimilarity()
    return _skill_similarity


def find_similar_skills(
    target: str,
    candidates: List[str],
    threshold: float = 0.3
) -> List[Tuple[str, float]]:
    """
    Convenience function to find similar skills.
    
    Args:
        target: Target skill
        candidates: Candidate skills
        threshold: Minimum similarity threshold
        
    Returns:
        List of (skill, score) tuples
    """
    return get_skill_similarity().find_similar_skills(
        target, candidates, threshold
    )


def find_closest_skill(query: str, options: List[str]) -> Optional[Tuple[str, float]]:
    """
    Convenience function to find closest matching skill.
    
    Args:
        query: Query string
        options: List of possible matches
        
    Returns:
        Tuple of (best_match, score) or None
    """
    return get_skill_similarity().find_closest_match(query, options)