"""
Pydantic models package.

This package exports all data models for the Skill Path Show API.
"""

from app.models.curriculum import (
    CurriculumInput,
    ExtractedSkill,
    CurriculumOutput
)

from app.models.roles import (
    RoleSkill,
    RoleProfile,
    RoleListResponse
)

from app.models.skills import (
    MatchedSkill,
    SkillGapInput,
    SkillGapOutput
)

from app.models.recommendations import (
    SubjectRecommendation,
    RecommendationInput,
    RecommendationOutput
)

from app.models.simulation import (
    SkillCoverage,
    SimulationInput,
    SimulationOutput
)

__all__ = [
    # Curriculum models
    "CurriculumInput",
    "ExtractedSkill",
    "CurriculumOutput",
    
    # Role models
    "RoleSkill",
    "RoleProfile",
    "RoleListResponse",
    
    # Skills models
    "MatchedSkill",
    "SkillGapInput",
    "SkillGapOutput",
    
    # Recommendations models
    "SubjectRecommendation",
    "RecommendationInput",
    "RecommendationOutput",
    
    # Simulation models
    "SkillCoverage",
    "SimulationInput",
    "SimulationOutput"
]