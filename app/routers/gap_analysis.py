"""
Skill gap analysis router.

This router handles the POST /analyze-gap endpoint
for identifying skill gaps between curriculum and target role.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.skills import SkillGapInput, SkillGapOutput
from app.services import get_gap_analysis_service

router = APIRouter()


@router.post(
    "/analyze-gap",
    response_model=SkillGapOutput,
    summary="Analyze Skill Gap",
    description="""
    Analyze the gap between extracted skills and target role requirements.
    
    This endpoint compares skills from a user's curriculum against
    the required skills for a target job role.
    
    ## Output Details
    - **matched_skills**: Skills present in both curriculum and role
    - **missing_skills**: Skills required by the role but not in curriculum
    - **gap_score**: Weighted coverage score (0-1)
      - 1.0 = Perfect match (all required skills present)
      - 0.0 = No match (all required skills missing)
    - **coverage_percentage**: Percentage of required skills covered
    """,
    tags=["Gap Analysis"]
)
async def analyze_gap(input_data: SkillGapInput) -> SkillGapOutput:
    """
    Analyze skill gap for a target role.
    
    Args:
        input_data: SkillGapInput with extracted_skills and target_role
        
    Returns:
        SkillGapOutput with matched, missing skills and gap score
        
    Raises:
        HTTPException: If target role not found
    """
    service = get_gap_analysis_service()
    
    try:
        result = service.analyze_gap(input_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing gap: {str(e)}"
        )


@router.post(
    "/analyze-gap/prioritize",
    summary="Get Priority Skills",
    description="""
    Get missing skills sorted by priority based on role weightages.
    
    Higher weightage skills are more important for the role.
    """,
    tags=["Gap Analysis"]
)
async def get_priority_skills(
    missing_skills: list,
    role_key: str
):
    """
    Get missing skills sorted by priority.
    
    Args:
        missing_skills: List of missing skill keys
        role_key: Target role key
        
    Returns:
        List of skills with priority levels
    """
    service = get_gap_analysis_service()
    priorities = service.get_priority_skills(missing_skills, role_key)
    
    return {
        "priorities": priorities,
        "count": len(priorities)
    }


@router.get(
    "/gap-analysis/health",
    summary="Gap Analysis Service Health",
    tags=["Gap Analysis"]
)
async def gap_analysis_health():
    """Health check for gap analysis service."""
    return {
        "status": "healthy",
        "service": "gap_analysis",
        "version": "1.0.0"
    }