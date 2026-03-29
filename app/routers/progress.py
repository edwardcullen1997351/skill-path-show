"""
Progress API endpoints for personalized learning paths.

This module provides endpoints for tracking learning progress,
marking subjects as completed, and viewing progress history.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional

from app.models.user import (
    LearningProgress,
    LearningProgressCreate,
    LearningProgressUpdate,
    CompletedSubject,
    CompletedSubjectCreate,
    RecommendationFeedback,
    RecommendationFeedbackCreate,
)
from app.services.progress_service import get_progress_service
from app.routers.user import get_current_user_id

router = APIRouter(prefix="/api/v1/users", tags=["progress"])


@router.get("/progress", response_model=List[LearningProgress])
async def get_user_progress(user_id: Optional[str] = None):
    """
    Get the current user's learning progress.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    progress = service.get_progress(user_id)
    return [LearningProgress(**p) for p in progress]


@router.post("/progress", response_model=LearningProgress, status_code=status.HTTP_201_CREATED)
async def create_progress_entry(
    progress: LearningProgressCreate,
    user_id: Optional[str] = None,
):
    """
    Create a new learning progress entry.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    try:
        created = service.create_progress(user_id, progress)
        return LearningProgress(**created)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create progress: {str(e)}",
        )


@router.put("/progress/{progress_id}", response_model=LearningProgress)
async def update_progress(
    progress_id: str,
    progress: LearningProgressUpdate,
    user_id: Optional[str] = None,
):
    """
    Update learning progress entry.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    try:
        updated = service.update_progress(user_id, progress_id, progress)
        return LearningProgress(**updated)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update progress: {str(e)}",
        )


@router.post("/subjects/complete", status_code=status.HTTP_201_CREATED)
async def mark_subject_complete(
    subject: CompletedSubjectCreate,
    user_id: Optional[str] = None,
):
    """
    Mark a subject as completed.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    try:
        completed = service.mark_completed(user_id, subject)
        return completed
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to mark subject complete: {str(e)}",
        )


@router.get("/subjects/completed", response_model=List[CompletedSubject])
async def get_completed_subjects(user_id: Optional[str] = None):
    """
    Get user's completed subjects.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    completed = service.get_completed_subjects(user_id)
    return [CompletedSubject(**c) for c in completed]


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def add_recommendation_feedback(
    feedback: RecommendationFeedbackCreate,
    user_id: Optional[str] = None,
):
    """
    Add feedback for a recommendation (for adaptive learning).
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    try:
        created = service.add_feedback(user_id, feedback)
        return created
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add feedback: {str(e)}",
        )


@router.get("/skill-coverage")
async def get_skill_coverage(
    target_role: str = "software_engineer",
    user_id: Optional[str] = None,
):
    """
    Get skill coverage based on completed subjects and skills.
    """
    service = get_progress_service()
    user_id = user_id or get_current_user_id()
    
    return service.get_skill_coverage(user_id, target_role)
