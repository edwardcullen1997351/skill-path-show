"""
Pydantic models for role profiles.

This module defines the data models for job role profiles
and their required skills.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class RoleSkill(BaseModel):
    """
    Model representing a single skill required for a role.
    
    Attributes:
        skill: The canonical skill name
        weightage: The importance of this skill for the role (0-1)
    """
    skill: str = Field(..., description="Canonical skill name")
    weightage: float = Field(
        ...,
        description="Weightage/importance of the skill (0-1)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill": "python",
                "weightage": 0.9
            }
        }


class RoleProfile(BaseModel):
    """
    Model representing a complete job role profile.
    
    Contains the role name, description, and all required skills
    with their weightages.
    """
    role_name: str = Field(..., description="Display name of the role")
    role_key: str = Field(..., description="Internal key for the role (e.g., 'frontend_developer')")
    required_skills: List[RoleSkill] = Field(
        ...,
        description="List of required skills with their weightages"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of the role"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "role_name": "Frontend Developer",
                "role_key": "frontend_developer",
                "required_skills": [
                    {"skill": "javascript", "weightage": 0.9},
                    {"skill": "html_css", "weightage": 0.85},
                    {"skill": "react", "weightage": 0.8}
                ],
                "description": "Builds user interfaces and web applications"
            }
        }


class RoleListResponse(BaseModel):
    """
    Response model for listing all available roles.
    """
    roles: List[str] = Field(
        ...,
        description="List of available role keys"
    )
    count: int = Field(..., description="Total number of roles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "roles": ["frontend_developer", "backend_developer", "data_analyst"],
                "count": 3
            }
        }