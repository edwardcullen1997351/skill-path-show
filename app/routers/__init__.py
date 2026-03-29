"""
Routers package for Skill Path Show API.

This package contains all API route handlers:
- curriculum: POST /parse-curriculum
- roles: GET /roles/{role_name}
- gap_analysis: POST /analyze-gap
- recommendations: POST /recommend-subjects
- simulation: POST /simulate-selection
"""

from app.routers import (
    curriculum,
    roles,
    gap_analysis,
    recommendations,
    simulation,
    similarity,
    llm,
    user,
    progress,
    adaptive,
)

__all__ = [
    "curriculum",
    "roles",
    "gap_analysis",
    "recommendations",
    "simulation",
    "similarity",
    "llm",
    "user",
    "progress",
    "adaptive",
]