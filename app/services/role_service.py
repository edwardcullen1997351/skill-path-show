"""
Role profile service.

This service handles retrieving role profiles and their required skills.
"""

from typing import List, Optional, Dict, Any
from app.models.roles import RoleProfile, RoleSkill, RoleListResponse
from app.utils.data_loader import get_data_loader
from app.utils.cache import get_role_cache


class RoleService:
    """
    Service for managing role profiles and required skills.
    """
    
    def __init__(self):
        """Initialize the role service."""
        self._data_loader = get_data_loader()
        self._cache = get_role_cache()
        self._local_cache: Dict[str, RoleProfile] = {}
    
    def get_role(self, role_name: str) -> Optional[RoleProfile]:
        """
        Get a role profile by role key/name.
        
        Args:
            role_name: Role key (e.g., 'frontend_developer') or display name
            
        Returns:
            RoleProfile or None if not found
        """
        # Check local cache first
        if role_name in self._local_cache:
            return self._local_cache[role_name]
        
        # Check global cache
        cached = self._cache.get(role_name)
        if cached is not None:
            self._local_cache[role_name] = cached
            return cached
        
        # Try to get from data loader
        role_data = self._data_loader.get_role_profile(role_name)
        
        if not role_data:
            return None
        
        # Convert to RoleProfile model
        role_profile = self._convert_to_model(role_data)
        
        # Cache it in both local and global cache
        self._local_cache[role_name] = role_profile
        self._cache.set(role_name, role_profile)
        
        return role_profile
    
    def get_all_roles(self) -> RoleListResponse:
        """
        Get list of all available roles.
        
        Returns:
            RoleListResponse with all role keys
        """
        role_keys = self._data_loader.get_all_roles()
        
        return RoleListResponse(
            roles=role_keys,
            count=len(role_keys)
        )
    
    def search_roles(self, query: str) -> List[RoleProfile]:
        """
        Search roles by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching role profiles
        """
        results: List[RoleProfile] = []
        all_roles = self._data_loader.get_all_roles()
        
        query_lower = query.lower()
        
        for role_key in all_roles:
            role = self.get_role(role_key)
            
            if role:
                # Check if query matches role name or description
                if (query_lower in role.role_name.lower() or
                    (role.description and query_lower in role.description.lower())):
                    results.append(role)
        
        return results
    
    def _convert_to_model(self, role_data: Dict[str, Any]) -> RoleProfile:
        """
        Convert role data dict to RoleProfile model.
        
        Args:
            role_data: Raw role data from JSON
            
        Returns:
            RoleProfile model
        """
        required_skills = []
        
        for skill_data in role_data.get("required_skills", []):
            required_skills.append(RoleSkill(
                skill=skill_data["skill"],
                weightage=skill_data["weightage"]
            ))
        
        return RoleProfile(
            role_name=role_data.get("role_name", ""),
            role_key=role_data.get("role_key", ""),
            required_skills=required_skills,
            description=role_data.get("description")
        )
    
    def get_role_skills(self, role_name: str) -> Optional[List[str]]:
        """
        Get list of required skill keys for a role.
        
        Args:
            role_name: Role key
            
        Returns:
            List of skill keys or None if role not found
        """
        role = self.get_role(role_name)
        
        if not role:
            return None
        
        return [skill.skill for skill in role.required_skills]
    
    def get_role_skill_weights(self, role_name: str) -> Optional[Dict[str, float]]:
        """
        Get dictionary of skill weights for a role.
        
        Args:
            role_name: Role key
            
        Returns:
            Dict of skill -> weight or None if role not found
        """
        role = self.get_role(role_name)
        
        if not role:
            return None
        
        return {
            skill.skill: skill.weightage 
            for skill in role.required_skills
        }
    
    def clear_cache(self) -> None:
        """Clear the role cache."""
        self._local_cache.clear()
        self._cache.clear()


# Create a global instance
_role_service: Optional[RoleService] = None


def get_role_service() -> RoleService:
    """
    Get the global role service instance.
    
    Returns:
        The singleton RoleService instance
    """
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service