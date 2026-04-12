"""
Skill Ontology Utilities.

This module provides functions for navigating the hierarchical
skill taxonomy and finding related skills.
"""

import os
import json
from typing import List, Dict, Optional, Any


def get_ontology_path() -> str:
    """Get the path to the ontology file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "skill_ontology.json")


class SkillOntology:
    """
    Skill ontology for hierarchical navigation.
    
    Provides methods for:
    - Getting parent/child skills
    - Finding related skills
    - Path traversal to root
    """
    
    def __init__(self):
        """Initialize the ontology."""
        self._ontology: Dict[str, Dict] = {}
        self._loaded = False
    
    def _load_ontology(self) -> bool:
        """Load the skill ontology from file."""
        if self._loaded:
            return True
        
        ontology_path = get_ontology_path()
        
        try:
            with open(ontology_path, "r") as f:
                self._ontology = json.load(f)
            self._loaded = True
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load ontology: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if ontology is loaded."""
        return self._load_ontology()
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get skill details.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Skill data or None
        """
        self._load_ontology()
        return self._ontology.get(skill_id)
    
    def get_parent(self, skill_id: str) -> Optional[str]:
        """
        Get parent skill ID.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Parent skill ID or None
        """
        skill = self.get_skill(skill_id)
        return skill.get("parent") if skill else None
    
    def get_children(self, skill_id: str) -> List[str]:
        """
        Get child skill IDs.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of child skill IDs
        """
        skill = self.get_skill(skill_id)
        return skill.get("children", []) if skill else []
    
    def get_related(self, skill_id: str) -> List[str]:
        """
        Get related skill IDs.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of related skill IDs
        """
        skill = self.get_skill(skill_id)
        return skill.get("related", []) if skill else []
    
    def get_path_to_root(self, skill_id: str) -> List[str]:
        """
        Get path from skill to root.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of skill IDs from root to skill
        """
        path = []
        current = skill_id
        
        visited = set()
        while current and current not in visited:
            visited.add(current)
            path.append(current)
            parent = self.get_parent(current)
            current = parent
        
        path.reverse()
        return path
    
    def get_level(self, skill_id: str) -> Optional[str]:
        """
        Get skill level (foundational, beginner, intermediate, advanced).
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Skill level or None
        """
        skill = self.get_skill(skill_id)
        return skill.get("level") if skill else None
    
    def get_name(self, skill_id: str) -> Optional[str]:
        """
        Get skill display name.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Skill name or None
        """
        skill = self.get_skill(skill_id)
        return skill.get("name") if skill else None
    
    def get_skill_with_details(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get skill with full details including relationships.
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Dict with skill details or None
        """
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        return {
            "skill_id": skill_id,
            "name": skill.get("name"),
            "level": skill.get("level"),
            "description": skill.get("description"),
            "parent": skill.get("parent"),
            "parent_name": self.get_name(skill.get("parent", "")) if skill.get("parent") else None,
            "children": skill.get("children", []),
            "children_names": [self.get_name(c) for c in skill.get("children", [])],
            "related": skill.get("related", []),
            "related_names": [self.get_name(r) for r in skill.get("related", [])]
        }
    
    def find_ancestors(self, skill_id: str) -> List[str]:
        """
        Find all ancestors (parent, grandparent, etc.).
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of ancestor skill IDs
        """
        return self.get_path_to_root(skill_id)[:-1]
    
    def find_descendants(self, skill_id: str) -> List[str]:
        """
        Find all descendants (children, grandchildren, etc.).
        
        Args:
            skill_id: Skill ID
            
        Returns:
            List of descendant skill IDs
        """
        descendants = []
        
        def collect_children(sid: str):
            children = self.get_children(sid)
            for child in children:
                descendants.append(child)
                collect_children(child)
        
        collect_children(skill_id)
        return descendants
    
    def get_root_skills(self) -> List[str]:
        """
        Get all root-level skills (no parent).
        
        Returns:
            List of root skill IDs
        """
        self._load_ontology()
        return [
            sid for sid, data in self._ontology.items()
            if data.get("parent") is None
        ]
    
    def get_all_skills(self) -> List[str]:
        """
        Get all skill IDs.
        
        Returns:
            List of all skill IDs
        """
        self._load_ontology()
        return list(self._ontology.keys())
    
    def get_skills_by_level(self, level: str) -> List[str]:
        """
        Get skills by level.
        
        Args:
            level: Level name (foundational, beginner, intermediate, advanced)
            
        Returns:
            List of skill IDs at that level
        """
        self._load_ontology()
        return [
            sid for sid, data in self._ontology.items()
            if data.get("level") == level
        ]
    
    def get_skill_tree(self, root_skill: Optional[str] = None) -> Dict:
        """
        Get skill tree starting from root or specified skill.
        
        Args:
            root_skill: Optional root skill ID
            
        Returns:
            Tree structure as dict
        """
        def build_tree(skill_id: str) -> Dict:
            skill = self.get_skill(skill_id)
            if not skill:
                return {}
            
            return {
                "skill_id": skill_id,
                "name": skill.get("name"),
                "level": skill.get("level"),
                "children": [build_tree(c) for c in skill.get("children", [])]
            }
        
        if root_skill:
            return build_tree(root_skill)
        
        roots = self.get_root_skills()
        return {
            "roots": [build_tree(r) for r in roots]
        }


_ontology: Optional[SkillOntology] = None


def get_skill_ontology() -> SkillOntology:
    """
    Get the global skill ontology instance.
    
    Returns:
        SkillOntology instance
    """
    global _ontology
    if _ontology is None:
        _ontology = SkillOntology()
    return _ontology


def get_skill_hierarchy(skill_id: str) -> Optional[Dict[str, Any]]:
    """
    Get skill with full hierarchy details.
    
    Args:
        skill_id: Skill ID
        
    Returns:
        Dict with hierarchy or None
    """
    return get_skill_ontology().get_skill_with_details(skill_id)


def get_related_skills(skill_id: str) -> List[Dict[str, str]]:
    """
    Get related skills with names.
    
    Args:
        skill_id: Skill ID
        
    Returns:
        List of {skill_id, name} dicts
    """
    ontology = get_skill_ontology()
    related_ids = ontology.get_related(skill_id)
    
    return [
        {"skill_id": rid, "name": ontology.get_name(rid)}
        for rid in related_ids
    ]