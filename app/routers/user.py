"""
User API endpoints for personalized learning paths.

This module provides endpoints for user profile management,
skill history, and preferences.
"""

from fastapi import APIRouter, HTTPException, status, Header
from typing import List, Optional

from app.models.user import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    SkillHistory,
    SkillHistoryCreate,
    UserPreferences,
    UserPreferencesUpdate,
    UserSkillsResponse,
    UserProgressSummary,
)
from app.services.user_service import get_user_service


router = APIRouter(prefix="/api/v1/users", tags=["users"])


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from authorization header.
    
    In production, this would validate JWT and extract user ID.
    For now, we'll use a simpler approach for development.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        # In production: decode JWT and extract user_id
        # For development: return token as user_id if it's a valid UUID
        return token
    # Default development user ID
    return "dev-user-id"


@router.post("/profile", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile: UserProfileCreate,
    user_id: Optional[str] = None,
):
    """
    Create a new user profile.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    try:
        created_profile = service.create_profile(user_id, profile)
        return UserProfile(**created_profile)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create profile: {str(e)}",
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(user_id: Optional[str] = None):
    """
    Get the current user's profile.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    profile = service.get_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    
    return UserProfile(**profile)


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile: UserProfileUpdate,
    user_id: Optional[str] = None,
):
    """
    Update the current user's profile.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    try:
        updated_profile = service.update_profile(user_id, profile)
        return UserProfile(**updated_profile)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update profile: {str(e)}",
        )


@router.get("/skills", response_model=UserSkillsResponse)
async def get_user_skills(user_id: Optional[str] = None):
    """
    Get the current user's skill history.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    skills = service.get_skill_history(user_id)
    return UserSkillsResponse(
        skills=[SkillHistory(**s) for s in skills],
        count=len(skills),
    )


@router.post("/skills", response_model=SkillHistory, status_code=status.HTTP_201_CREATED)
async def add_user_skill(
    skill: SkillHistoryCreate,
    user_id: Optional[str] = None,
):
    """
    Add a skill to the user's history.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    try:
        created_skill = service.add_skill(user_id, skill)
        return SkillHistory(**created_skill)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add skill: {str(e)}",
        )


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_skill(
    skill_id: str,
    user_id: Optional[str] = None,
):
    """
    Remove a skill from the user's history.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    success = service.remove_skill(user_id, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: Optional[str] = None):
    """
    Get the current user's preferences.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    preferences = service.get_preferences(user_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )
    
    return UserPreferences(**preferences)


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    user_id: Optional[str] = None,
):
    """
    Update the current user's preferences.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    try:
        updated_preferences = service.update_preferences(user_id, preferences)
        return UserPreferences(**updated_preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update preferences: {str(e)}",
        )


@router.get("/progress-summary", response_model=UserProgressSummary)
async def get_progress_summary(
    target_role: str = "software_engineer",
    total_subjects: int = 12,
    user_id: Optional[str] = None,
):
    """
    Get a summary of the user's learning progress.
    """
    service = get_user_service()
    user_id = user_id or get_current_user_id()
    
    return service.get_progress_summary(user_id, target_role, total_subjects)
