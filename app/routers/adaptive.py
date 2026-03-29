"""
Adaptive recommendation API endpoints.

This module provides endpoints for adaptive recommendations that use
collaborative filtering and Q-learning to personalize subject recommendations.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, List

from app.models.user import AdaptiveRecommendationRequest
from app.services.adaptive_service import get_adaptive_service
from app.services.progress_service import get_progress_service
from app.routers.user import get_current_user_id

router = APIRouter(prefix="/api/v1/recommendations", tags=["adaptive"])


@router.post("/adaptive")
async def get_adaptive_recommendations(
    request: AdaptiveRecommendationRequest,
    user_id: Optional[str] = None,
    missing_skills: Optional[List[str]] = None,
):
    """
    Get adaptive recommendations based on user history and preferences.
    
    This endpoint uses:
    - MECE algorithm for base recommendations
    - Collaborative filtering to find similar users' choices
    - Q-learning to optimize based on user feedback
    
    Args:
        request: Recommendation request with target role and options
        user_id: Optional user ID override
        missing_skills: Optional list of missing skills
        
    Returns:
        Personalized recommendations with algorithm metadata
    """
    service = get_adaptive_service()
    user_id = user_id or get_current_user_id()
    
    # Get missing skills from progress service if not provided
    if not missing_skills:
        progress_service = get_progress_service()
        coverage = progress_service.get_skill_coverage(user_id, request.target_role)
        missing_skills = coverage.get("missing", [])
    
    if not missing_skills:
        missing_skills = ["python", "sql", "data_analysis"]  # Default skills
    
    try:
        recommendations = service.get_adaptive_recommendations(
            user_id=user_id,
            target_role=request.target_role,
            missing_skills=missing_skills,
            use_collaborative=request.use_collaborative,
            use_rl=request.use_rl,
            top_k=request.top_k,
        )
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get recommendations: {str(e)}",
        )


@router.post("/feedback")
async def record_recommendation_feedback(
    subject_code: str,
    user_action: str,
    user_id: Optional[str] = None,
):
    """
    Record user feedback for a recommendation.
    
    This feedback is used to improve future recommendations through
    Q-learning. User actions:
    - "accepted": User selected the recommended subject
    - "rejected": User rejected the recommendation
    - "ignored": User saw but didn't interact with the recommendation
    """
    service = get_adaptive_service()
    user_id = user_id or get_current_user_id()
    
    if user_action not in ["accepted", "rejected", "ignored"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_action. Must be: accepted, rejected, or ignored",
        )
    
    try:
        service.record_feedback(user_id, subject_code, user_action)
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to record feedback: {str(e)}",
        )


@router.get("/similar-users/{target_role}")
async def get_similar_users(
    target_role: str,
    user_id: Optional[str] = None,
):
    """
    Get users with similar profiles and their completed subjects.
    
    This is useful for understanding what subjects similar users completed
    and can inform collaborative filtering recommendations.
    """
    service = get_adaptive_service()
    user_id = user_id or get_current_user_id()
    
    from app.utils.supabase_client import get_supabase_client
    client = get_supabase_client()
    
    # Find similar users
    response = (
        client.table("user_profiles")
        .select("id, role_goal")
        .eq("role_goal", target_role)
        .neq("id", user_id)
        .execute()
    )
    
    if not response.data:
        return {"similar_users": [], "message": "No similar users found"}
    
    # Get their completed subjects
    similar_user_ids = [u["id"] for u in response.data[:10]]  # Limit to 10
    completions = (
        client.table("completed_subjects")
        .select("user_id, subject_code, grade")
        .in_("user_id", similar_user_ids)
        .execute()
    )
    
    # Group by user
    user_subjects = {}
    for c in completions.data:
        uid = c["user_id"]
        if uid not in user_subjects:
            user_subjects[uid] = []
        user_subjects[uid].append({
            "subject_code": c["subject_code"],
            "grade": c.get("grade"),
        })
    
    return {
        "similar_users": [
            {"user_id": uid, "completed_subjects": subjects}
            for uid, subjects in user_subjects.items()
        ],
    }
