"""
User service for personalized learning paths.

This module provides CRUD operations for user profiles, skill histories,
preferences, and learning progress using Supabase.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.models.user import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    SkillHistory,
    SkillHistoryCreate,
    UserPreferences,
    UserPreferencesUpdate,
    UserProgressSummary,
)
from app.utils.supabase_client import get_supabase_client


class UserService:
    """Service for user profile operations."""
    
    def __init__(self, client: Optional[Client] = None):
        """Initialize user service."""
        self._client = client or get_supabase_client()
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        response = self._client.table("user_profiles").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None
    
    def create_profile(self, user_id: str, profile: UserProfileCreate) -> Dict[str, Any]:
        """Create a new user profile."""
        data = {
            "id": user_id,
            "email": profile.email,
            "role_goal": profile.role_goal,
            "experience_level": profile.experience_level,
            "career_interests": profile.career_interests,
        }
        response = self._client.table("user_profiles").insert(data).execute()
        return response.data[0]
    
    def update_profile(self, user_id: str, profile: UserProfileUpdate) -> Dict[str, Any]:
        """Update user profile."""
        update_data = profile.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = (
            self._client.table("user_profiles")
            .update(update_data)
            .eq("id", user_id)
            .execute()
        )
        return response.data[0]
    
    def get_skill_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's skill history."""
        response = (
            self._client.table("skill_histories")
            .select("*")
            .eq("user_id", user_id)
            .order("acquired_at", desc=True)
            .execute()
        )
        return response.data
    
    def add_skill(self, user_id: str, skill: SkillHistoryCreate) -> Dict[str, Any]:
        """Add a skill to user's history."""
        data = {
            "user_id": user_id,
            "skill_name": skill.skill_name,
            "proficiency": skill.proficiency,
            "source_subject": skill.source_subject,
        }
        response = self._client.table("skill_histories").insert(data).execute()
        return response.data[0]
    
    def remove_skill(self, user_id: str, skill_id: str) -> bool:
        """Remove a skill from user's history."""
        response = (
            self._client.table("skill_histories")
            .delete()
            .eq("id", skill_id)
            .eq("user_id", user_id)
            .execute()
        )
        return len(response.data) > 0
    
    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        response = (
            self._client.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0] if response.data else None
    
    def update_preferences(
        self, user_id: str, preferences: UserPreferencesUpdate
    ) -> Dict[str, Any]:
        """Update user preferences."""
        update_data = preferences.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = (
            self._client.table("user_preferences")
            .update(update_data)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0]
    
    def get_progress_summary(
        self,
        user_id: str,
        target_role: str,
        total_subjects: int = 12,
    ) -> UserProgressSummary:
        """Get a summary of user's learning progress."""
        # Get completed subjects
        completed_response = (
            self._client.table("completed_subjects")
            .select("subject_code, completed_at, grade")
            .eq("user_id", user_id)
            .execute()
        )
        completed_subjects = completed_response.data
        
        # Get user profile for career path
        profile = self.get_profile(user_id)
        career_path = profile.get("role_goal") if profile else target_role
        
        # Calculate progress
        completed_count = len(completed_subjects)
        overall_progress = (completed_count / total_subjects) * 100 if total_subjects > 0 else 0
        
        # Get skill coverage
        skills_response = self.get_skill_history(user_id)
        covered_skills = [s["skill_name"] for s in skills_response]
        
        return UserProgressSummary(
            user_id=user_id,
            overall_progress=overall_progress,
            completed_subjects=completed_count,
            total_subjects=total_subjects,
            skill_coverage={
                "covered": covered_skills,
                "in_progress": [],
                "missing": [],
            },
            career_path=career_path,
            next_milestone=None,
            estimated_completion=None,
        )


# Global instance
_user_service: Optional[UserService] = None


def get_user_service(client: Optional[Client] = None) -> UserService:
    """Get the global user service instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserService(client)
    return _user_service
