"""
Recommendation router.

This router handles the POST /recommend-subjects endpoint
for generating MECE subject recommendations.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.recommendations import (
    RecommendationInput,
    RecommendationOutput,
    LearningPathInput,
    LearningPathOutput
)
from app.services import get_recommendation_service
from app.utils.mece_algorithm import get_mece_extended

router = APIRouter()


@router.post(
    "/recommend-subjects",
    response_model=RecommendationOutput,
    summary="Generate MECE Recommendations",
    description="""
    Generate a minimal set of subject recommendations that:
    - **Collectively Exhaustive**: Cover all missing skills
    - **Mutually Exclusive**: Minimize skill overlap between subjects
    
    ## Algorithm
    Uses a greedy set cover algorithm that:
    1. Calculates the marginal contribution of each subject
    2. Applies redundancy penalty for overlapping skills
    3. Selects subject with highest net contribution
    4. Repeats until all skills covered
    
    ## Output Details
    - **selected_subjects**: Recommended subjects with coverage details
    - **total_coverage**: Ratio of skills covered (0-1)
    - **remaining_gaps**: Skills not covered by any subject
    """,
    tags=["Recommendations"]
)
async def recommend_subjects(input_data: RecommendationInput) -> RecommendationOutput:
    """
    Generate MECE subject recommendations.
    
    Args:
        input_data: RecommendationInput with missing_skills
        
    Returns:
        RecommendationOutput with selected subjects and coverage
        
    Raises:
        HTTPException: If no missing skills provided
    """
    if not input_data.missing_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing skills list cannot be empty"
        )
    
    service = get_recommendation_service()
    
    try:
        result = service.generate_recommendations(input_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.post(
    "/recommend-subjects/alternatives",
    summary="Get Alternative Recommendations",
    description="""
    Get alternative recommendations excluding specific subjects.
    
    Useful for exploring different learning paths.
    """,
    tags=["Recommendations"]
)
async def get_alternatives(
    missing_skills: list,
    exclude_subjects: list
):
    """
    Get alternative recommendations.
    
    Args:
        missing_skills: Skills that need coverage
        exclude_subjects: Subjects to exclude
        
    Returns:
        Alternative recommendations
    """
    service = get_recommendation_service()
    
    result = service.get_alternative_recommendations(
        missing_skills=missing_skills,
        exclude_subjects=exclude_subjects
    )
    
    return result


@router.get(
    "/recommendations/health",
    summary="Recommendation Service Health",
    tags=["Recommendations"]
)
async def recommendations_health():
    """Health check for recommendation service."""
    return {
        "status": "healthy",
        "service": "recommendations",
        "version": "1.0.0"
    }


@router.post(
    "/generate-learning-path",
    response_model=LearningPathOutput,
    summary="Generate Learning Path with MECE++",
    description="""
    Generate an optimized learning path with:
    - **MECE++ Algorithm**: Extended greedy set cover with cost constraints
    - **Sequence Optimization**: Topological sort respecting prerequisites
    - **Time Budgeting**: Split into terms based on weekly hours
    
    ## Features
    - Automatically includes prerequisites
    - Respects credit limits per term
    - Orders subjects by dependency
    - Provides complete duration estimates
    
    ## Output Details
    - **learning_path**: Subjects organized by term with hours/credits
    - **total_coverage**: Ratio of skills covered (0-1)
    - **summary**: Total duration, hours, and credits
    """,
    tags=["Learning Path"]
)
async def generate_learning_path(input_data: LearningPathInput) -> LearningPathOutput:
    """
    Generate a complete learning path with sequence optimization.
    
    Args:
        input_data: LearningPathInput with missing_skills and constraints
        
    Returns:
        LearningPathOutput with ordered subjects and duration
        
    Raises:
        HTTPException: If no missing skills provided
    """
    if not input_data.missing_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing skills list cannot be empty"
        )
    
    mece_extended = get_mece_extended()
    
    try:
        result = mece_extended.generate_learning_plan(
            missing_skills=input_data.missing_skills,
            weekly_hours=input_data.weekly_hours,
            max_credits_per_term=input_data.max_credits_per_term,
            weeks_per_term=input_data.weeks_per_term,
            include_prerequisites=input_data.include_prerequisites
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating learning path: {str(e)}"
        )