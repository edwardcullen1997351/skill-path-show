"""
Skill normalizer module for mapping raw skill terms to canonical skills.

This module provides functions to normalize skill names by mapping
synonyms and variations to canonical skill identifiers.
"""

from typing import Dict, List, Set, Optional
from app.utils.data_loader import get_data_loader
from app.utils.nlp_utils import tokenize, clean_text


class SkillNormalizer:
    """
    Skill normalizer that maps raw skill text to canonical skill names.
    
    Uses the skills taxonomy to find matching canonical skills for
    given raw skill terms.
    """
    
    def __init__(self):
        """Initialize the skill normalizer with the data loader."""
        self._data_loader = get_data_loader()
        self._taxonomy: Optional[Dict] = None
        self._reverse_map: Optional[Dict[str, str]] = None
    
    def _load_taxonomy(self) -> None:
        """Load the skills taxonomy and build reverse mapping."""
        if self._taxonomy is None:
            self._taxonomy = self._data_loader.load_skills_taxonomy()
            self._build_reverse_map()
    
    def _build_reverse_map(self) -> None:
        """
        Build reverse mapping from synonyms to canonical skills.
        
        This creates a dictionary where keys are all possible synonyms
        and values are the canonical skill names.
        """
        self._reverse_map = {}
        
        for category, skills in self._taxonomy.items():
            for canonical_skill, synonyms in skills.items():
                # Add canonical skill as itself
                self._reverse_map[canonical_skill.lower()] = canonical_skill
                
                # Add all synonyms
                for synonym in synonyms:
                    self._reverse_map[synonym.lower()] = canonical_skill
    
    def normalize(self, raw_skill: str) -> str:
        """
        Normalize a raw skill term to its canonical form.
        
        Args:
            raw_skill: Raw skill text (e.g., 'python programming', 'js', 'React')
            
        Returns:
            Canonical skill name (e.g., 'python', 'javascript', 'react')
        """
        self._load_taxonomy()
        
        # Clean the input
        cleaned = clean_text(raw_skill)
        
        # Try direct match first
        if cleaned.lower() in self._reverse_map:
            return self._reverse_map[cleaned.lower()]
        
        # Try matching individual tokens
        tokens = tokenize(cleaned)
        
        # Check for multi-word matches
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens) + 1):
                phrase = ' '.join(tokens[i:j])
                if phrase.lower() in self._reverse_map:
                    return self._reverse_map[phrase.lower()]
        
        # Try partial matches
        for key in self._reverse_map:
            if key in cleaned or cleaned in key:
                return self._reverse_map[key]
        
        # Return the cleaned input as-is if no match found
        return cleaned
    
    def normalize_batch(self, raw_skills: List[str]) -> List[str]:
        """
        Normalize a batch of raw skill terms.
        
        Args:
            raw_skills: List of raw skill texts
            
        Returns:
            List of canonical skill names
        """
        return [self.normalize(skill) for skill in raw_skills]
    
    def get_all_canonical_skills(self) -> List[str]:
        """
        Get list of all canonical skill names.
        
        Returns:
            List of canonical skill names
        """
        self._load_taxonomy()
        
        canonical_skills = set()
        for category, skills in self._taxonomy.items():
            canonical_skills.update(skills.keys())
        
        return sorted(list(canonical_skills))
    
    def get_skill_category(self, skill: str) -> Optional[str]:
        """
        Get the category of a canonical skill.
        
        Args:
            skill: Canonical skill name
            
        Returns:
            Category name or None if not found
        """
        self._load_taxonomy()
        
        for category, skills in self._taxonomy.items():
            if skill in skills:
                return category
        
        return None
    
    def get_skill_synonyms(self, skill: str) -> List[str]:
        """
        Get all synonyms for a canonical skill.
        
        Args:
            skill: Canonical skill name
            
        Returns:
            List of synonyms including the canonical form
        """
        self._load_taxonomy()
        
        for category, skills in self._taxonomy.items():
            if skill in skills:
                return [skill] + skills[skill]
        
        return [skill]
    
    def is_known_skill(self, skill: str) -> bool:
        """
        Check if a skill is in the taxonomy.
        
        Args:
            skill: Skill to check
            
        Returns:
            True if the skill is known, False otherwise
        """
        self._load_taxonomy()
        
        normalized = self.normalize(skill)
        return normalized in self._reverse_map


# Create a global instance
_skill_normalizer: Optional[SkillNormalizer] = None


def get_skill_normalizer() -> SkillNormalizer:
    """
    Get the global skill normalizer instance.
    
    Returns:
        The singleton SkillNormalizer instance
    """
    global _skill_normalizer
    if _skill_normalizer is None:
        _skill_normalizer = SkillNormalizer()
    return _skill_normalizer


def normalize_skill(raw_skill: str) -> str:
    """
    Convenience function to normalize a single skill.
    
    Args:
        raw_skill: Raw skill text
        
    Returns:
        Canonical skill name
    """
    return get_skill_normalizer().normalize(raw_skill)


def normalize_skills(raw_skills: List[str]) -> List[str]:
    """
    Convenience function to normalize multiple skills.
    
    Args:
        raw_skills: List of raw skill texts
        
    Returns:
        List of canonical skill names
    """
    return get_skill_normalizer().normalize_batch(raw_skills)