"""
User models for personalized learning paths.

This module provides Pydantic models for user profiles, skill histories,
preferences, and learning progress.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class UserProfile(BaseModel):
    """User profile model."""
    id: str
    email: Optional[str] = None
    role_goal: Optional[str] = None
    experience_level: str = "beginner"
    career_interests: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProfileCreate(BaseModel):
    """Model for creating a user profile."""
    email: str
    role_goal: Optional[str] = None
    experience_level: Optional[str] = "beginner"
    career_interests: Optional[List[str]] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    """Model for updating a user profile."""
    role_goal: Optional[str] = None
    experience_level: Optional[str] = None
    career_interests: Optional[List[str]] = None


class SkillHistory(BaseModel):
    """User skill history model."""
    id: Optional[str] = None
    user_id: str
    skill_name: str
    proficiency: str = "intermediate"
    acquired_at: Optional[datetime] = None
    source_subject: Optional[str] = None
    created_at: Optional[datetime] = None


class SkillHistoryCreate(BaseModel):
    """Model for creating a skill history entry."""
    skill_name: str
    proficiency: Optional[str] = "intermediate"
    source_subject: Optional[str] = None


class LearningProgress(BaseModel):
    """Learning progress model."""
    id: Optional[str] = None
    user_id: str
    subject_code: str
    subject_name: Optional[str] = None
    status: str = "not_started"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LearningProgressCreate(BaseModel):
    """Model for creating a learning progress entry."""
    subject_code: str
    subject_name: Optional[str] = None
    status: Optional[str] = "not_started"


class LearningProgressUpdate(BaseModel):
    """Model for updating learning progress."""
    status: Optional[str] = None
    score: Optional[float] = None


class UserPreferences(BaseModel):
    """User preferences model."""
    id: Optional[str] = None
    user_id: str
    learning_style: str = "visual"
    weekly_hours: int = 10
    difficulty_preference: str = "balanced"
    avoided_skills: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPreferencesUpdate(BaseModel):
    """Model for updating user preferences."""
    learning_style: Optional[str] = None
    weekly_hours: Optional[int] = None
    difficulty_preference: Optional[str] = None
    avoided_skills: Optional[List[str]] = None


class CompletedSubject(BaseModel):
    """Completed subject model."""
    id: Optional[str] = None
    user_id: str
    subject_code: str
    completed_at: Optional[datetime] = None
    grade: Optional[float] = None


class CompletedSubjectCreate(BaseModel):
    """Model for creating a completed subject entry."""
    subject_code: str
    grade: Optional[float] = None


class RecommendationFeedback(BaseModel):
    """Recommendation feedback model."""
    id: Optional[str] = None
    user_id: str
    subject_code: str
    was_recommended: bool = True
    user_action: Optional[str] = None
    created_at: Optional[datetime] = None


class RecommendationFeedbackCreate(BaseModel):
    """Model for creating recommendation feedback."""
    subject_code: str
    was_recommended: Optional[bool] = True
    user_action: str


class UserProgressSummary(BaseModel):
    """Summary of user progress for visualization."""
    user_id: str
    overall_progress: float
    completed_subjects: int
    total_subjects: int
    skill_coverage: dict
    career_path: Optional[str] = None
    next_milestone: Optional[str] = None
    estimated_completion: Optional[str] = None


class UserSkillsResponse(BaseModel):
    """Response model for user skills."""
    skills: List[SkillHistory]
    count: int


class UserProgressResponse(BaseModel):
    """Response model for user progress."""
    progress: List[LearningProgress]
    count: int


class AdaptiveRecommendationRequest(BaseModel):
    """Request model for adaptive recommendations."""
    target_role: str
    use_collaborative: bool = True
    use_rl: bool = False
    top_k: int = 5
