"""
LLM Integration router.

This router provides endpoints for using Google Gemini LLM
for enhanced curriculum parsing and recommendations.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.utils.llm_service import get_gemini_service, is_llm_available
from app.utils.data_loader import get_data_loader

router = APIRouter()


class LLMParseInput(BaseModel):
    """Input for LLM curriculum parsing."""
    curriculum_text: str
    use_llm: bool = True


class LLMExplanationInput(BaseModel):
    """Input for LLM explanation generation."""
    missing_skills: List[str]
    recommended_subjects: List[Dict[str, Any]]
    target_role: str


class InterviewTopicsInput(BaseModel):
    """Input for interview topic suggestion."""
    skills: List[str]
    role: str


@router.get(
    "/llm-status",
    summary="Check LLM Availability",
    description="Check if Google Gemini API is configured and available",
    tags=["LLM"]
)
async def get_llm_status():
    """
    Check LLM availability.
    
    Returns:
        Status of LLM integration
    """
    available = is_llm_available()
    
    return {
        "llm_available": available,
        "provider": "Google Gemini" if available else None,
        "message": "LLM is ready to use" if available else "Set GOOGLE_API_KEY environment variable to enable LLM"
    }


@router.post(
    "/llm-parse-curriculum",
    summary="Parse Curriculum with LLM",
    description="""
    Use Google Gemini to parse curriculum and extract skills.
    
    This provides more intelligent parsing than the basic NLP approach.
    Requires GOOGLE_API_KEY environment variable to be set.
    """,
    tags=["LLM"]
)
async def parse_curriculum_llm(input_data: LLMParseInput):
    """
    Parse curriculum using Gemini LLM.
    
    Args:
        input_data: Curriculum text to parse
        
    Returns:
        Extracted skills and subjects from LLM
    """
    if not is_llm_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not available. Set GOOGLE_API_KEY environment variable."
        )
    
    gemini = get_gemini_service()
    data_loader = get_data_loader()
    
    # Get taxonomy for context
    taxonomy = data_loader.load_skills_taxonomy()
    
    # Call LLM
    result = gemini.parse_curriculum_with_llm(
        curriculum_text=input_data.curriculum_text,
        skill_taxonomy=taxonomy
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse curriculum with LLM"
        )
    
    return {
        "success": True,
        "skills": result.skills,
        "subjects": result.subjects,
        "proficiency_level": result.proficiency_level,
        "raw_response": result.raw_response[:500] if result.raw_response else None
    }


@router.post(
    "/llm-explain-recommendations",
    summary="Generate Recommendation Explanation",
    description="""
    Use Gemini to generate a natural language explanation
    for why certain subjects are recommended.
    """,
    tags=["LLM"]
)
async def explain_recommendations(input_data: LLMExplanationInput):
    """
    Generate explanation for recommendations.
    
    Args:
        input_data: Missing skills and recommended subjects
        
    Returns:
        Natural language explanation
    """
    if not is_llm_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not available. Set GOOGLE_API_KEY environment variable."
        )
    
    gemini = get_gemini_service()
    
    explanation = gemini.generate_recommendation_explanation(
        missing_skills=input_data.missing_skills,
        recommended_subjects=input_data.recommended_subjects,
        target_role=input_data.target_role
    )
    
    if explanation is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation with LLM"
        )
    
    return {
        "success": True,
        "explanation": explanation,
        "target_role": input_data.target_role
    }


@router.post(
    "/llm-interview-topics",
    summary="Suggest Interview Topics",
    description="""
    Use Gemini to suggest technical interview preparation topics
    based on the skills gap.
    """,
    tags=["LLM"]
)
async def suggest_interview_topics(input_data: InterviewTopicsInput):
    """
    Suggest interview preparation topics.
    
    Args:
        input_data: Skills and target role
        
    Returns:
        List of interview topics
    """
    if not is_llm_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not available. Set GOOGLE_API_KEY environment variable."
        )
    
    gemini = get_gemini_service()
    
    topics = gemini.suggest_interview_topics(
        skills=input_data.skills,
        role=input_data.role
    )
    
    if topics is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview topics with LLM"
        )
    
    return {
        "success": True,
        "topics": topics,
        "role": input_data.role
    }


@router.post(
    "/llm-normalize-skill",
    summary="Normalize Skill with LLM",
    description="""
    Use Gemini to normalize a skill name to its canonical form.
    """,
    tags=["LLM"]
)
async def normalize_skill_llm(raw_skill: str, known_skills: List[str]):
    """
    Normalize a skill using LLM.
    
    Args:
        raw_skill: Raw skill text
        known_skills: List of known canonical skills
        
    Returns:
        Normalized skill name
    """
    if not is_llm_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not available. Set GOOGLE_API_KEY environment variable."
        )
    
    gemini = get_gemini_service()
    
    normalized = gemini.normalize_skill_with_llm(
        raw_skill=raw_skill,
        known_skills=known_skills
    )
    
    if normalized is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to normalize skill with LLM"
        )
    
    return {
        "success": True,
        "raw_skill": raw_skill,
        "normalized_skill": normalized
    }