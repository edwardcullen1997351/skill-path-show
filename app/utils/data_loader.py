"""
Data loader module for loading JSON data files.

This module provides utilities to load and cache the data files
used by the application (skills taxonomy, role profiles, subjects catalog).
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class DataLoader:
    """
    Singleton data loader for loading JSON data files.
    
    Uses caching to avoid repeated file reads.
    """
    
    _instance: Optional['DataLoader'] = None
    _cache: Dict[str, Any] = {}
    _base_path: Path = Path(__file__).parent.parent / "data"
    
    def __new__(cls) -> 'DataLoader':
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_skills_taxonomy(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load skills taxonomy from JSON file.
        
        Returns:
            Dict containing skills taxonomy with synonyms mapping
        """
        if "skills_taxonomy" not in self._cache:
            with open(self._base_path / "skills_taxonomy.json", "r") as f:
                self._cache["skills_taxonomy"] = json.load(f)
        return self._cache["skills_taxonomy"]
    
    def load_role_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Load role profiles from JSON file.
        
        Returns:
            Dict containing role profiles with required skills
        """
        if "role_profiles" not in self._cache:
            with open(self._base_path / "role_profiles.json", "r") as f:
                self._cache["role_profiles"] = json.load(f)
        return self._cache["role_profiles"]
    
    def load_subjects_catalog(self) -> List[Dict[str, Any]]:
        """
        Load subjects catalog from JSON file.
        
        Returns:
            List of subject dictionaries
        """
        if "subjects_catalog" not in self._cache:
            with open(self._base_path / "subjects_catalog.json", "r") as f:
                data = json.load(f)
                self._cache["subjects_catalog"] = data.get("subjects", [])
        return self._cache["subjects_catalog"]
    
    def get_role_profile(self, role_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific role profile by key.
        
        Args:
            role_key: The role key to look up
            
        Returns:
            Role profile dict or None if not found
        """
        profiles = self.load_role_profiles()
        return profiles.get(role_key)
    
    def get_subject_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a subject by its name.
        
        Args:
            name: Subject name
            
        Returns:
            Subject dict or None if not found
        """
        subjects = self.load_subjects_catalog()
        for subject in subjects:
            if subject.get("name") == name:
                return subject
        return None
    
    def get_subject_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get a subject by its code.
        
        Args:
            code: Subject code (e.g., 'CS301')
            
        Returns:
            Subject dict or None if not found
        """
        subjects = self.load_subjects_catalog()
        for subject in subjects:
            if subject.get("code") == code:
                return subject
        return None
    
    def get_all_roles(self) -> List[str]:
        """
        Get list of all available role keys.
        
        Returns:
            List of role keys
        """
        profiles = self.load_role_profiles()
        return list(profiles.keys())
    
    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()


# Create a global instance
data_loader = DataLoader()


def get_data_loader() -> DataLoader:
    """
    Get the global data loader instance.
    
    Returns:
        The singleton DataLoader instance
    """
    return data_loader