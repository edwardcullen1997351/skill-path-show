"""
Pydantic models for MECE subject recommendations.

This module defines the data models for generating
minimal, mutually exclusive and collectively exhaustive
subject recommendations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SubjectRecommendation(BaseModel):
    """
    Model representing a recommended subject with its coverage details.
    
    Attributes:
        subject_name: Name of the recommended subject
        covered_skills: List of skills covered by this subject
        marginal_contribution: How much this subject adds to coverage (0-1)
        redundancy_penalty: Penalty for overlapping with other subjects (0-1)
    """
    subject_name: str = Field(..., description="Name of the subject")
    subject_code: str = Field(..., description="Subject code")
    covered_skills: List[str] = Field(
        ...,
        description="List of skills this subject covers"
    )
    marginal_contribution: float = Field(
        ...,
        description="Marginal contribution score (0-1)",
        ge=0.0,
        le=1.0
    )
    redundancy_penalty: float = Field(
        default=0.0,
        description="Redundancy penalty for overlapping skills (0-1)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject_name": "Web Development Fundamentals",
                "subject_code": "CS301",
                "covered_skills": ["html_css", "javascript", "responsive_design"],
                "marginal_contribution": 0.85,
                "redundancy_penalty": 0.0
            }
        }


class RecommendationInput(BaseModel):
    """
    Input model for subject recommendation.
    
    Attributes:
        missing_skills: List of skills that need to be covered
        preferred_subjects: Optional list of preferred subject codes
    """
    missing_skills: List[str] = Field(
        ...,
        description="List of skills that need to be covered",
        min_length=1
    )
    preferred_subjects: Optional[List[str]] = Field(
        default=None,
        description="Optional list of preferred subject codes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "missing_skills": ["react", "responsive_design", "api_design"]
            }
        }


class RecommendationOutput(BaseModel):
    """
    Output model for subject recommendations.
    
    Contains the selected subjects and their coverage details.
    """
    selected_subjects: List[SubjectRecommendation] = Field(
        ...,
        description="List of recommended subjects"
    )
    total_coverage: float = Field(
        ...,
        description="Total coverage of missing skills (0-1)",
        ge=0.0,
        le=1.0
    )
    remaining_gaps: List[str] = Field(
        ...,
        description="Skills that could not be covered by any subject"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_subjects": [
                    {
                        "subject_name": "Web Development Fundamentals",
                        "subject_code": "CS301",
                        "covered_skills": ["html_css", "javascript", "responsive_design"],
                        "marginal_contribution": 0.85,
                        "redundancy_penalty": 0.0
                    }
                ],
                "total_coverage": 0.85,
                "remaining_gaps": []
            }
        }