"""
Pydantic models for coverage simulation.

This module defines the data models for simulating
skill coverage based on selected subjects.
"""

from typing import List
from pydantic import BaseModel, Field


class SkillCoverage(BaseModel):
    """
    Model representing coverage status of a single skill.
    
    Attributes:
        skill: The skill name
        covered: Whether this skill is covered by selected subjects
        weightage: The weightage of this skill for the target role
        source_subjects: List of subjects that cover this skill
    """
    skill: str = Field(..., description="Skill name")
    covered: bool = Field(..., description="Whether the skill is covered")
    weightage: float = Field(
        ...,
        description="Weightage of the skill for the role",
        ge=0.0,
        le=1.0
    )
    source_subjects: List[str] = Field(
        default_factory=list,
        description="Subjects that provide this skill"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill": "javascript",
                "covered": True,
                "weightage": 0.9,
                "source_subjects": ["React Development"]
            }
        }


class SimulationInput(BaseModel):
    """
    Input model for coverage simulation.
    
    Attributes:
        selected_subjects: List of subject names to simulate
        target_role: The target job role key
    """
    selected_subjects: List[str] = Field(
        ...,
        description="List of selected subject names",
        min_length=1
    )
    target_role: str = Field(
        ...,
        description="Target role key (e.g., 'frontend_developer')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_subjects": ["React Development", "Database Systems"],
                "target_role": "frontend_developer"
            }
        }


class SimulationOutput(BaseModel):
    """
    Output model for coverage simulation.
    
    Contains the updated coverage percentage, remaining gaps,
    and detailed skill coverage breakdown.
    """
    updated_coverage_percent: float = Field(
        ...,
        description="Updated coverage percentage (0-100)",
        ge=0.0,
        le=100.0
    )
    remaining_gaps: List[str] = Field(
        ...,
        description="Skills not covered by selected subjects"
    )
    skill_coverage_breakdown: List[SkillCoverage] = Field(
        ...,
        description="Detailed breakdown of each skill's coverage"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "updated_coverage_percent": 68.5,
                "remaining_gaps": ["html_css", "git"],
                "skill_coverage_breakdown": [
                    {
                        "skill": "javascript",
                        "covered": True,
                        "weightage": 0.9,
                        "source_subjects": ["React Development"]
                    },
                    {
                        "skill": "html_css",
                        "covered": False,
                        "weightage": 0.85,
                        "source_subjects": []
                    }
                ]
            }
        }