"""
Curriculum processing router.

This router handles the POST /parse-curriculum endpoint
for extracting skills from college curricula.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.curriculum import CurriculumInput, CurriculumOutput
from app.services import get_curriculum_service

router = APIRouter()


@router.post(
    "/parse-curriculum",
    response_model=CurriculumOutput,
    summary="Parse Curriculum",
    description="""
    Extract skills from college curriculum text or structured data.
    
    Supports three input formats:
    - **text**: Raw curriculum text (e.g., from PDF extraction)
    - **subjects**: List of subject codes (e.g., ['CS201', 'CS301'])
    - **raw_json**: Structured JSON curriculum data
    
    The endpoint uses NLP techniques to:
    - Identify subjects mentioned in the text
    - Extract skill keywords
    - Normalize skill names using the skills taxonomy
    - Determine skill proficiency levels
    """,
    response_description="Extracted subjects and skills from the curriculum",
    status_code=status.HTTP_200_OK,
    tags=["Curriculum"]
)
async def parse_curriculum(input_data: CurriculumInput) -> CurriculumOutput:
    """
    Parse curriculum input and extract skills.
    
    Args:
        input_data: CurriculumInput with text, subjects, or raw_json
        
    Returns:
        CurriculumOutput with extracted subjects and skills
        
    Raises:
        HTTPException: If input validation fails
    """
    # Validate input
    if not input_data.text and not input_data.subjects and not input_data.raw_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of 'text', 'subjects', or 'raw_json' must be provided"
        )
    
    # Get service
    service = get_curriculum_service()
    
    try:
        # Parse curriculum
        result = service.parse_curriculum(input_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing curriculum: {str(e)}"
        )


@router.get(
    "/curriculum/health",
    summary="Curriculum Service Health",
    description="Check if the curriculum processing service is healthy",
    tags=["Curriculum"]
)
async def curriculum_health():
    """Health check for curriculum service."""
    return {
        "status": "healthy",
        "service": "curriculum",
        "version": "1.0.0"
    }