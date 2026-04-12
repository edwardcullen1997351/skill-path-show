"""
LLM Integration router.

This router provides endpoints for using multiple LLM providers
(Gemini, OpenAI, Anthropic, Ollama) for parsing and recommendations.
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.utils.llm_unified import get_llm_service
from app.utils.data_loader import get_data_loader
from app.providers import list_available_providers, get_provider

router = APIRouter()


class LLMParseInput(BaseModel):
    """Input for LLM curriculum parsing."""
    curriculum_text: str
    provider: Optional[str] = "gemini"
    model: Optional[str] = None
    use_fine_tuned: bool = Field(default=False, description="Use domain-optimized prompts")


class LLMExplanationInput(BaseModel):
    """Input for LLM explanation generation."""
    missing_skills: List[str]
    recommended_subjects: List[Dict[str, Any]]
    target_role: str
    provider: Optional[str] = None


class InterviewTopicsInput(BaseModel):
    """Input for interview topic suggestion."""
    skills: List[str]
    role: str
    provider: Optional[str] = None


class ProviderSelectInput(BaseModel):
    """Input for selecting a provider."""
    provider: str
    model: Optional[str] = None


@router.get(
    "/llm-providers",
    summary="List Available LLM Providers",
    description="Get a list of all available LLM providers and their status",
    tags=["LLM"]
)
async def list_providers():
    """
    List all available LLM providers.
    
    Returns:
        Dict of providers with their availability status
    """
    available = list_available_providers()
    service = get_llm_service()
    status_info = service.get_status()
    
    return {
        "providers": status_info["providers"],
        "default_provider": status_info["default_provider"]
    }


@router.post(
    "/llm-providers/select",
    summary="Select LLM Provider",
    description="Set the active LLM provider for subsequent requests",
    tags=["LLM"]
)
async def select_provider(input_data: ProviderSelectInput):
    """
    Select an LLM provider.
    
    Args:
        input_data: Provider selection data
        
    Returns:
        Confirmation of provider selection
    """
    provider = get_provider(input_data.provider)
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{input_data.provider}' not found"
        )
    
    if not provider.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{input_data.provider}' is not available. Check API keys."
        )
    
    service = get_llm_service()
    success = service.set_provider(input_data.provider)
    
    if success:
        return {
            "success": True,
            "provider": input_data.provider,
            "model": input_data.model or provider.model
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to set provider '{input_data.provider}'"
        )


@router.get(
    "/llm-status",
    summary="Check LLM Availability",
    description="Check which LLM providers are configured and available",
    tags=["LLM"]
)
async def get_llm_status():
    """
    Check LLM availability.
    
    Returns:
        Status of LLM integration
    """
    available = list_available_providers()
    
    active_providers = [name for name, is_available in available.items() if is_available]
    
    return {
        "available_providers": active_providers,
        "all_providers": available,
        "message": f"Available: {', '.join(active_providers) if active_providers else 'None'}"
    }


@router.post(
    "/llm-parse-curriculum",
    summary="Parse Curriculum with LLM",
    description="""
    Use an LLM to parse curriculum and extract skills.
    
    Specify the provider (gemini, openai, anthropic, ollama) to use.
    Set use_fine_tuned=true for domain-optimized prompts with few-shot examples.
    Requires appropriate API key environment variable to be set.
    """,
    tags=["LLM"]
)
async def parse_curriculum_llm(input_data: LLMParseInput):
    """
    Parse curriculum using LLM.
    
    Args:
        input_data: Curriculum text and provider selection
        
    Returns:
        Extracted skills and subjects from LLM
    """
    service = get_llm_service()
    
    if not service.set_provider(input_data.provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{input_data.provider}' is not available. Check API keys."
        )
    
    data_loader = get_data_loader()
    taxonomy = data_loader.load_skills_taxonomy()
    
    result = service.parse_curriculum(
        curriculum_text=input_data.curriculum_text,
        skill_taxonomy=taxonomy,
        provider=input_data.provider,
        use_fine_tuned=input_data.use_fine_tuned
    )
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse curriculum with {input_data.provider}"
        )
    
    return {
        "success": True,
        "provider": input_data.provider,
        "use_fine_tuned": input_data.use_fine_tuned,
        "skills": result.get("skills", []),
        "subjects": result.get("subjects", []),
        "proficiency_level": result.get("proficiency_level", "intermediate")
    }


@router.post(
    "/llm-explain-recommendations",
    summary="Generate Recommendation Explanation",
    description="""
    Use an LLM to generate a natural language explanation
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
    service = get_llm_service()
    
    provider = input_data.provider or "gemini"
    if not service.set_provider(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not available"
        )
    
    explanation = service.generate_explanation(
        missing_skills=input_data.missing_skills,
        recommended_subjects=input_data.recommended_subjects,
        target_role=input_data.target_role,
        provider=provider
    )
    
    if explanation is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation with {provider}"
        )
    
    return {
        "success": True,
        "provider": provider,
        "explanation": explanation,
        "target_role": input_data.target_role
    }


@router.post(
    "/llm-interview-topics",
    summary="Suggest Interview Topics",
    description="""
    Use an LLM to suggest technical interview preparation topics
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
    service = get_llm_service()
    
    provider = input_data.provider or "gemini"
    if not service.set_provider(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not available"
        )
    
    topics = service.suggest_interview_topics(
        skills=input_data.skills,
        role=input_data.role,
        provider=provider
    )
    
    if topics is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview topics with {provider}"
        )
    
    return {
        "success": True,
        "provider": provider,
        "topics": topics,
        "role": input_data.role
    }


@router.get(
    "/llm-compare",
    summary="Compare LLM Providers",
    description="Compare outputs from multiple LLM providers",
    tags=["LLM"]
)
async def compare_providers(
    prompt: str = Query(..., description="Prompt to send to providers"),
    providers: str = Query(default="gemini,openai", description="Comma-separated provider names")
):
    """
    Compare outputs from multiple providers.
    
    Args:
        prompt: Prompt to send
        providers: List of providers to compare
        
    Returns:
        Dict of provider responses
    """
    provider_list = [p.strip() for p in providers.split(",")]
    service = get_llm_service()
    
    results = service.compare_providers(prompt, provider_list)
    
    return {
        "prompt": prompt,
        "results": {
            name: {
                "available": resp is not None,
                "response": resp.text[:500] if resp else None
            }
            for name, resp in results.items()
        }
    }


@router.post(
    "/llm-normalize-skill",
    summary="Normalize Skill with LLM",
    description="""
    Use an LLM to normalize a skill name to its canonical form.
    """,
    tags=["LLM"]
)
async def normalize_skill_llm(
    raw_skill: str = Query(..., description="Raw skill text"),
    known_skills: str = Query(..., description="Comma-separated known skills"),
    provider: str = Query(default="gemini", description="Provider to use")
):
    """
    Normalize a skill using LLM.
    
    Args:
        raw_skill: Raw skill text
        known_skills: Comma-separated list of known canonical skills
        provider: LLM provider to use
        
    Returns:
        Normalized skill name
    """
    service = get_llm_service()
    
    if not service.set_provider(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not available"
        )
    
    known_list = [s.strip() for s in known_skills.split(",")]
    
    normalized = service.normalize_skill(
        raw_skill=raw_skill,
        known_skills=known_list,
        provider=provider
    )
    
    if normalized is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to normalize skill with {provider}"
        )
    
    return {
        "success": True,
        "provider": provider,
        "raw_skill": raw_skill,
        "normalized_skill": normalized
    }