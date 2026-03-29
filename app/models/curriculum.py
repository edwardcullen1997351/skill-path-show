"""
Pydantic models for curriculum processing.

This module defines the data models for parsing curriculum text
and extracting skills from it.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class CurriculumInput(BaseModel):
    """
    Input model for curriculum parsing endpoint.
    
    Supports multiple input formats:
    - Raw text (e.g., from PDF extraction)
    - Subject codes list
    - Structured JSON data
    """
    text: Optional[str] = Field(
        default=None,
        description="Raw curriculum text (e.g., 'Data Structures, Algorithms, Python Programming')"
    )
    subjects: Optional[List[str]] = Field(
        default=None,
        description="List of subject codes (e.g., ['CS201', 'CS301'])"
    )
    raw_json: Optional[Dict] = Field(
        default=None,
        description="Structured JSON curriculum data"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Data Structures, Algorithms, Python Programming, Web Development with React",
                "subjects": ["CS201", "CS301"]
            }
        }


class ExtractedSkill(BaseModel):
    """
    Model representing a single extracted skill from the curriculum.
    
    Attributes:
        skill: The canonical skill name (e.g., 'python', 'react')
        proficiency: Skill proficiency level (basic, intermediate, advanced)
        source: The subject/course from which the skill was extracted
    """
    skill: str = Field(..., description="Canonical skill name")
    proficiency: str = Field(
        ...,
        description="Proficiency level: basic, intermediate, or advanced",
        pattern="^(basic|intermediate|advanced)$"
    )
    source: str = Field(..., description="Source subject or course name")
    

class CurriculumOutput(BaseModel):
    """
    Output model for curriculum parsing endpoint.
    
    Contains the list of subjects found and skills extracted.
    """
    subjects: List[str] = Field(
        ...,
        description="List of identified subjects/courses"
    )
    extracted_skills: List[ExtractedSkill] = Field(
        ...,
        description="List of extracted skills with proficiency levels"
    )
    skill_proficiency: str = Field(
        ...,
        description="Overall skill proficiency level of the curriculum"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "subjects": [
                    "Data Structures and Algorithms",
                    "Web Development Fundamentals",
                    "Database Systems"
                ],
                "extracted_skills": [
                    {"skill": "algorithms", "proficiency": "intermediate", "source": "Data Structures and Algorithms"},
                    {"skill": "react", "proficiency": "basic", "source": "Web Development Fundamentals"},
                    {"skill": "sql", "proficiency": "intermediate", "source": "Database Systems"}
                ],
                "skill_proficiency": "intermediate"
            }
        }