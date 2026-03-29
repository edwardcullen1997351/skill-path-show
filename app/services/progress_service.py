"""
Progress tracking service for personalized learning paths.

This module provides functionality to track user learning progress,
mark subjects as completed, and calculate skill coverage.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import Client

from app.models.user import (
    LearningProgress,
    LearningProgressCreate,
    LearningProgressUpdate,
    CompletedSubject,
    CompletedSubjectCreate,
    RecommendationFeedback,
    RecommendationFeedbackCreate,
)
from app.utils.supabase_client import get_supabase_client


class ProgressService:
    """Service for tracking learning progress."""
    
    def __init__(self, client: Optional[Client] = None):
        """Initialize progress service."""
        self._client = client or get_supabase_client()
    
    def get_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's learning progress."""
        response = (
            self._client.table("learning_progress")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    
    def create_progress(
        self, user_id: str, progress: LearningProgressCreate
    ) -> Dict[str, Any]:
        """Create a new learning progress entry."""
        data = {
            "user_id": user_id,
            "subject_code": progress.subject_code,
            "subject_name": progress.subject_name,
            "status": progress.status or "not_started",
        }
        
        if progress.status == "in_progress":
            data["started_at"] = datetime.utcnow().isoformat()
        
        response = self._client.table("learning_progress").insert(data).execute()
        return response.data[0]
    
    def update_progress(
        self, user_id: str, progress_id: str, progress: LearningProgressUpdate
    ) -> Dict[str, Any]:
        """Update learning progress."""
        update_data = progress.model_dump(exclude_unset=True)
        
        # Handle status changes
        if "status" in update_data:
            if update_data["status"] == "in_progress" and progress_id:
                existing = self._client.table("learning_progress").select("started_at").eq("id", progress_id).execute()
                if existing.data and not existing.data[0].get("started_at"):
                    update_data["started_at"] = datetime.utcnow().isoformat()
            elif update_data["status"] == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = (
            self._client.table("learning_progress")
            .update(update_data)
            .eq("id", progress_id)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data[0]
    
    def mark_completed(
        self, user_id: str, subject: CompletedSubjectCreate
    ) -> Dict[str, Any]:
        """Mark a subject as completed."""
        data = {
            "user_id": user_id,
            "subject_code": subject.subject_code,
            "completed_at": datetime.utcnow().isoformat(),
            "grade": subject.grade,
        }
        
        # Upsert (insert or update if exists)
        response = self._client.table("completed_subjects").upsert(data).execute()
        
        # Also update the learning progress entry
        self._client.table("learning_progress").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "score": subject.grade,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("user_id", user_id).eq("subject_code", subject.subject_code).execute()
        
        return response.data[0] if response.data else data
    
    def get_completed_subjects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's completed subjects."""
        response = (
            self._client.table("completed_subjects")
            .select("*")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .execute()
        )
        return response.data
    
    def add_feedback(
        self, user_id: str, feedback: RecommendationFeedbackCreate
    ) -> Dict[str, Any]:
        """Add feedback for a recommendation."""
        data = {
            "user_id": user_id,
            "subject_code": feedback.subject_code,
            "was_recommended": feedback.was_recommended,
            "user_action": feedback.user_action,
        }
        
        response = self._client.table("recommendation_feedback").insert(data).execute()
        return response.data[0]
    
    def get_skill_coverage(
        self, user_id: str, target_role: str
    ) -> Dict[str, List[str]]:
        """Calculate skill coverage based on completed subjects."""
        # Get completed subjects
        completed = self.get_completed_subjects(user_id)
        completed_codes = [s["subject_code"] for s in completed]
        
        # Get user's skills
        skills_response = (
            self._client.table("skill_histories")
            .select("skill_name")
            .eq("user_id", user_id)
            .execute()
        )
        covered_skills = [s["skill_name"] for s in skills_response.data]
        
        # Get role requirements
        role_response = (
            self._client.table("role_profiles")
            .select("required_skills")
            .eq("role_key", target_role)
            .execute()
        )
        
        required_skills = []
        if role_response.data:
            required_skills = [s["skill"] for s in role_response.data[0].get("required_skills", [])]
        
        # Calculate coverage
        in_progress = []  # Could track in-progress subjects
        missing = [s for s in required_skills if s not in covered_skills]
        
        return {
            "covered": covered_skills,
            "in_progress": in_progress,
            "missing": missing,
        }


# Global instance
_progress_service: Optional[ProgressService] = None


def get_progress_service(client: Optional[Client] = None) -> ProgressService:
    """Get the global progress service instance."""
    global _progress_service
    if _progress_service is None:
        _progress_service = ProgressService(client)
    return _progress_service
