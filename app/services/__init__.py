"""
Services package for Skill Path Show API.

This package contains all business logic services:
- CurriculumService: Parse and extract skills from curriculum
- RoleService: Manage role profiles and required skills
- GapAnalysisService: Analyze skill gaps
- RecommendationService: Generate MECE recommendations
- SimulationService: Simulate skill coverage
"""

from app.services.curriculum_service import (
    CurriculumService,
    get_curriculum_service
)

from app.services.role_service import (
    RoleService,
    get_role_service
)

from app.services.gap_service import (
    GapAnalysisService,
    get_gap_analysis_service
)

from app.services.recommendation_service import (
    RecommendationService,
    get_recommendation_service
)

from app.services.simulation_service import (
    SimulationService,
    get_simulation_service
)

__all__ = [
    # Curriculum service
    "CurriculumService",
    "get_curriculum_service",
    
    # Role service
    "RoleService",
    "get_role_service",
    
    # Gap analysis service
    "GapAnalysisService",
    "get_gap_analysis_service",
    
    # Recommendation service
    "RecommendationService",
    "get_recommendation_service",
    
    # Simulation service
    "SimulationService",
    "get_simulation_service"
]