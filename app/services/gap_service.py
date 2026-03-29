"""
Skill gap analysis service.

This service handles analyzing gaps between extracted skills
and target role requirements.
"""

from typing import List, Optional, Dict
from app.models.skills import (
    SkillGapInput,
    SkillGapOutput,
    MatchedSkill
)
from app.services.role_service import get_role_service
from app.utils.skill_normalizer import get_skill_normalizer


class GapAnalysisService:
    """
    Service for analyzing skill gaps between curriculum and target role.
    """
    
    def __init__(self):
        """Initialize the gap analysis service."""
        self._role_service = get_role_service()
        self._skill_normalizer = get_skill_normalizer()
    
    def analyze_gap(self, input_data: SkillGapInput) -> SkillGapOutput:
        """
        Analyze gap between extracted skills and target role requirements.
        
        Args:
            input_data: Gap analysis input with extracted skills and target role
            
        Returns:
            SkillGapOutput with matched, missing, and partial skills
        """
        # Get role profile
        role = self._role_service.get_role(input_data.target_role)
        
        if not role:
            raise ValueError(f"Role '{input_data.target_role}' not found")
        
        # Normalize extracted skills
        normalized_skills = self._skill_normalizer.normalize_batch(
            input_data.extracted_skills
        )
        
        # Get required skills with weights
        required_skill_weights = {
            skill.skill: skill.weightage 
            for skill in role.required_skills
        }
        
        # Categorize skills
        matched_skills: List[MatchedSkill] = []
        missing_skills: List[str] = []
        partial_skills: List[MatchedSkill] = []
        
        matched_weights = 0.0
        total_weights = sum(required_skill_weights.values())
        
        for skill_key, weight in required_skill_weights.items():
            if skill_key in normalized_skills:
                matched_skills.append(MatchedSkill(
                    skill=skill_key,
                    weightage=weight,
                    matched=True
                ))
                matched_weights += weight
            else:
                missing_skills.append(skill_key)
        
        # Calculate gap score (weighted coverage)
        gap_score = matched_weights / total_weights if total_weights > 0 else 0.0
        
        # Calculate coverage percentage
        coverage_percentage = gap_score * 100
        
        # Sort matched skills by weight (highest first)
        matched_skills.sort(key=lambda x: x.weightage, reverse=True)
        
        return SkillGapOutput(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            partial_skills=partial_skills,
            gap_score=round(gap_score, 3),
            coverage_percentage=round(coverage_percentage, 2)
        )
    
    def get_gap_severity(self, gap_score: float) -> str:
        """
        Get severity level of the gap.
        
        Args:
            gap_score: Gap score (0-1)
            
        Returns:
            Severity: 'low', 'medium', 'high', 'critical'
        """
        if gap_score >= 0.8:
            return "low"
        elif gap_score >= 0.6:
            return "medium"
        elif gap_score >= 0.4:
            return "high"
        else:
            return "critical"
    
    def get_priority_skills(
        self,
        missing_skills: List[str],
        role_key: str
    ) -> List[Dict]:
        """
        Get missing skills sorted by priority (weightage).
        
        Args:
            missing_skills: List of missing skill keys
            role_key: Target role key
            
        Returns:
            List of dicts with skill and priority info
        """
        role = self._role_service.get_role(role_key)
        
        if not role:
            return []
        
        # Create priority list
        priorities = []
        
        for skill in role.required_skills:
            if skill.skill in missing_skills:
                priorities.append({
                    "skill": skill.skill,
                    "weightage": skill.weightage,
                    "priority": self._calculate_priority(skill.weightage)
                })
        
        # Sort by weightage (descending)
        priorities.sort(key=lambda x: x.weightage, reverse=True)
        
        return priorities
    
    def _calculate_priority(self, weightage: float) -> str:
        """
        Calculate priority level based on weightage.
        
        Args:
            weightage: Skill weightage (0-1)
            
        Returns:
            Priority: 'high', 'medium', 'low'
        """
        if weightage >= 0.8:
            return "high"
        elif weightage >= 0.5:
            return "medium"
        else:
            return "low"


# Create a global instance
_gap_analysis_service: Optional[GapAnalysisService] = None


def get_gap_analysis_service() -> GapAnalysisService:
    """
    Get the global gap analysis service instance.
    
    Returns:
        The singleton GapAnalysisService instance
    """
    global _gap_analysis_service
    if _gap_analysis_service is None:
        _gap_analysis_service = GapAnalysisService()
    return _gap_analysis_service