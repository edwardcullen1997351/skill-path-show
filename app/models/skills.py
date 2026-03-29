"""
Pydantic models for skill gap analysis.

This module defines the data models for analyzing gaps between
extracted skills and target role requirements.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MatchedSkill(BaseModel):
    """
    Model representing a skill and its matching status.
    
    Attributes:
        skill: The skill name
        weightage: The weightage of this skill for the role
        matched: Whether the skill is present in the user's profile
    """
    skill: str = Field(..., description="Skill name")
    weightage: float = Field(
        ...,
        description="Weightage of the skill for the target role",
        ge=0.0,
        le=1.0
    )
    matched: bool = Field(..., description="Whether the skill is matched")


class SkillGapInput(BaseModel):
    """
    Input model for skill gap analysis.
    
    Attributes:
        extracted_skills: List of skills extracted from the user's curriculum
        target_role: The target job role key (e.g., 'frontend_developer')
    """
    extracted_skills: List[str] = Field(
        ...,
        description="List of skills from the user's curriculum",
        min_length=1
    )
    target_role: str = Field(
        ...,
        description="Target role key (e.g., 'frontend_developer')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "extracted_skills": ["python", "sql", "data_analysis", "statistics"],
                "target_role": "data_analyst"
            }
        }


class SkillGapOutput(BaseModel):
    """
    Output model for skill gap analysis.
    
    Contains matched skills, missing skills, partial matches,
    and an overall gap score.
    """
    matched_skills: List[MatchedSkill] = Field(
        ...,
        description="Skills that are present in both curriculum and role"
    )
    missing_skills: List[str] = Field(
        ...,
        description="Skills required by the role but not in the curriculum"
    )
    partial_skills: List[MatchedSkill] = Field(
        default_factory=list,
        description="Skills that partially match (if any)"
    )
    gap_score: float = Field(
        ...,
        description="Gap score (0-1, where 1 means perfect match)",
        ge=0.0,
        le=1.0
    )
    coverage_percentage: float = Field(
        ...,
        description="Percentage of required skills covered",
        ge=0.0,
        le=100.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "matched_skills": [
                    {"skill": "python", "weightage": 0.9, "matched": True},
                    {"skill": "sql", "weightage": 0.85, "matched": True},
                    {"skill": "data_analysis", "weightage": 0.9, "matched": True},
                    {"skill": "statistics", "weightage": 0.75, "matched": True}
                ],
                "missing_skills": ["data_visualization"],
                "partial_skills": [],
                "gap_score": 0.89,
                "coverage_percentage": 88.75
            }
        }