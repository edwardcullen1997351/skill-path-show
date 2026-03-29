"""
Recommendation service.

This service handles generating MECE subject recommendations
based on missing skills.
"""

from typing import Optional
from app.models.recommendations import (
    RecommendationInput,
    RecommendationOutput,
    SubjectRecommendation
)
from app.utils.mece_algorithm import get_mece_engine


class RecommendationService:
    """
    Service for generating subject recommendations.
    """
    
    def __init__(self):
        """Initialize the recommendation service."""
        self._mece_engine = get_mece_engine()
    
    def generate_recommendations(
        self,
        input_data: RecommendationInput
    ) -> RecommendationOutput:
        """
        Generate MECE subject recommendations for missing skills.
        
        Args:
            input_data: Recommendation input with missing skills
            
        Returns:
            RecommendationOutput with selected subjects and coverage
        """
        # Get recommendations from MECE engine
        result = self._mece_engine.generate_recommendations(
            missing_skills=input_data.missing_skills,
            preferred_subjects=input_data.preferred_subjects
        )
        
        # Convert to output model
        selected_subjects = []
        
        for subj in result.get("selected_subjects", []):
            selected_subjects.append(SubjectRecommendation(
                subject_name=subj.get("subject_name", ""),
                subject_code=subj.get("subject_code", ""),
                covered_skills=subj.get("covered_skills", []),
                marginal_contribution=subj.get("marginal_contribution", 0.0),
                redundancy_penalty=subj.get("redundancy_penalty", 0.0)
            ))
        
        return RecommendationOutput(
            selected_subjects=selected_subjects,
            total_coverage=result.get("total_coverage", 0.0),
            remaining_gaps=result.get("remaining_gaps", [])
        )
    
    def get_alternative_recommendations(
        self,
        missing_skills: list,
        exclude_subjects: list
    ) -> RecommendationOutput:
        """
        Get alternative recommendations excluding specific subjects.
        
        Args:
            missing_skills: Skills that need coverage
            exclude_subjects: Subject names to exclude
            
        Returns:
            Alternative recommendations
        """
        # This would require modifying the MECE engine to exclude subjects
        # For now, we return the regular recommendations
        input_data = RecommendationInput(missing_skills=missing_skills)
        return self.generate_recommendations(input_data)


# Create a global instance
_recommendation_service: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """
    Get the global recommendation service instance.
    
    Returns:
        The singleton RecommendationService instance
    """
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    return _recommendation_service