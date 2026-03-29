"""
Coverage simulation service.

This service handles simulating skill coverage based on
selected subjects for a target role.
"""

from typing import Optional
from app.models.simulation import (
    SimulationInput,
    SimulationOutput,
    SkillCoverage
)
from app.utils.mece_algorithm import get_mece_engine


class SimulationService:
    """
    Service for simulating skill coverage with selected subjects.
    """
    
    def __init__(self):
        """Initialize the simulation service."""
        self._mece_engine = get_mece_engine()
    
    def simulate_coverage(
        self,
        input_data: SimulationInput
    ) -> SimulationOutput:
        """
        Simulate skill coverage for selected subjects.
        
        Args:
            input_data: Simulation input with selected subjects and target role
            
        Returns:
            SimulationOutput with coverage details
        """
        # Get coverage breakdown from MECE engine
        result = self._mece_engine.get_coverage_breakdown(
            selected_subject_names=input_data.selected_subjects,
            role_key=input_data.target_role
        )
        
        # Handle error case
        if "error" in result:
            return SimulationOutput(
                updated_coverage_percent=0.0,
                remaining_gaps=[],
                skill_coverage_breakdown=[]
            )
        
        # Convert to output model
        skill_coverage = []
        
        for item in result.get("skill_coverage_breakdown", []):
            skill_coverage.append(SkillCoverage(
                skill=item.get("skill", ""),
                covered=item.get("covered", False),
                weightage=item.get("weightage", 0.0),
                source_subjects=item.get("source_subjects", [])
            ))
        
        return SimulationOutput(
            updated_coverage_percent=result.get("updated_coverage_percent", 0.0),
            remaining_gaps=result.get("remaining_gaps", []),
            skill_coverage_breakdown=skill_coverage
        )
    
    def calculate_optimal_additions(
        self,
        current_subjects: list,
        target_role: str,
        max_additions: int = 3
    ) -> list:
        """
        Calculate which subjects would optimally increase coverage.
        
        Args:
            current_subjects: Currently selected subjects
            target_role: Target role key
            max_additions: Maximum number of subjects to recommend
            
        Returns:
            List of recommended subjects to add
        """
        # Get role profile to find required skills
        from app.services.role_service import get_role_service
        role_service = get_role_service()
        role = role_service.get_role(target_role)
        
        if not role:
            return []
        
        # Get skills covered by current subjects
        covered_skills = set()
        
        for subj_name in current_subjects:
            from app.utils.data_loader import get_data_loader
            data_loader = get_data_loader()
            subject = data_loader.get_subject_by_name(subj_name)
            
            if subject:
                covered_skills.update(subject.get("covered_skills", []))
        
        # Find missing skills
        required_skills = {skill.skill for skill in role.required_skills}
        missing_skills = required_skills - covered_skills
        
        if not missing_skills:
            return []
        
        # Generate recommendations for missing skills
        from app.models.recommendations import RecommendationInput
        input_data = RecommendationInput(missing_skills=list(missing_skills))
        
        from app.services.recommendation_service import get_recommendation_service
        rec_service = get_recommendation_service()
        recommendations = rec_service.generate_recommendations(input_data)
        
        # Return top N subjects
        return [
            {
                "subject_name": subj.subject_name,
                "subject_code": subj.subject_code,
                "marginal_contribution": subj.marginal_contribution
            }
            for subj in recommendations.selected_subjects[:max_additions]
        ]


# Create a global instance
_simulation_service: Optional[SimulationService] = None


def get_simulation_service() -> SimulationService:
    """
    Get the global simulation service instance.
    
    Returns:
        The singleton SimulationService instance
    """
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service