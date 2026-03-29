"""
MECE (Mutually Exclusive, Collectively Exhaustive) Recommendation Algorithm.

This module implements a greedy set cover algorithm to generate minimal
subject recommendations that:
- Collectively Exhaustive: Cover all missing skills
- Mutually Exclusive: Minimize skill overlap/redundancy
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from app.utils.data_loader import get_data_loader


class MECERecommendationEngine:
    """
    MECE Recommendation Engine using greedy set cover algorithm.
    
    The algorithm finds a minimal set of subjects that covers all
    required skills while minimizing overlap between subjects.
    """
    
    # Penalty factor for redundancy (10% per overlapping skill)
    REDUNDANCY_PENALTY = 0.10
    
    # Maximum redundancy penalty cap (50% of marginal contribution)
    MAX_PENALTY_RATIO = 0.5
    
    def __init__(self):
        """Initialize the MECE engine with data loader."""
        self._data_loader = get_data_loader()
    
    def calculate_marginal_contribution(
        self,
        subject: Dict[str, Any],
        uncovered_skills: Set[str],
        selected_subjects: List[Dict[str, Any]]
    ) -> Tuple[float, float]:
        """
        Calculate the marginal contribution of adding a subject.
        
        Args:
            subject: Subject to evaluate
            uncovered_skills: Set of skills that still need coverage
            selected_subjects: List of already selected subjects
            
        Returns:
            Tuple of (marginal_contribution, redundancy_penalty)
        """
        subject_skills = set(subject.get("covered_skills", []))
        
        # Calculate new skills covered
        new_skills = subject_skills & uncovered_skills
        
        if not new_skills:
            return 0.0, 0.0
        
        # Marginal contribution: ratio of new skills to uncovered skills
        marginal = len(new_skills) / len(uncovered_skills)
        
        # Calculate redundancy penalty
        redundancy_penalty = 0.0
        for sel_subject in selected_subjects:
            sel_skills = set(sel_subject.get("covered_skills", []))
            overlap = subject_skills & sel_skills
            
            # Penalize each overlapping skill
            redundancy_penalty += len(overlap) * self.REDUNDANCY_PENALTY
        
        # Cap penalty to prevent negative scores
        max_penalty = marginal * self.MAX_PENALTY_RATIO
        redundancy_penalty = min(redundancy_penalty, max_penalty)
        
        return marginal, redundancy_penalty
    
    def get_net_score(
        self,
        subject: Dict[str, Any],
        uncovered_skills: Set[str],
        selected_subjects: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate the net score for a subject.
        
        Net score = marginal_contribution - redundancy_penalty
        
        Args:
            subject: Subject to score
            uncovered_skills: Set of skills that still need coverage
            selected_subjects: List of already selected subjects
            
        Returns:
            Net score (0-1)
        """
        marginal, penalty = self.calculate_marginal_contribution(
            subject, uncovered_skills, selected_subjects
        )
        
        return marginal - penalty
    
    def find_best_subject(
        self,
        subjects: List[Dict[str, Any]],
        uncovered_skills: Set[str],
        selected_subjects: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the subject with the highest net score.
        
        Args:
            subjects: List of available subjects
            uncovered_skills: Set of skills that still need coverage
            selected_subjects: List of already selected subjects
            
        Returns:
            Best subject or None if no subject can cover any skill
        """
        best_subject = None
        best_score = -1
        
        for subject in subjects:
            score = self.get_net_score(subject, uncovered_skills, selected_subjects)
            
            if score > best_score:
                best_score = score
                best_subject = subject
        
        return best_subject
    
    def generate_recommendations(
        self,
        missing_skills: List[str],
        preferred_subjects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate MECE subject recommendations.
        
        Uses greedy set cover algorithm to find minimal subject set
        that covers all missing skills.
        
        Args:
            missing_skills: List of skills that need coverage
            preferred_subjects: Optional list of preferred subject codes
            
        Returns:
            Dict containing selected subjects, coverage, and remaining gaps
        """
        # Load subjects catalog
        all_subjects = self._data_loader.load_subjects_catalog()
        
        # Filter to preferred subjects if specified
        if preferred_subjects:
            subjects = [
                s for s in all_subjects 
                if s.get("code") in preferred_subjects
            ]
            # If no preferred subjects found, fall back to all
            if not subjects:
                subjects = all_subjects
        else:
            subjects = all_subjects
        
        # Initialize tracking variables
        uncovered_skills = set(missing_skills)
        selected_subjects: List[Dict[str, Any]] = []
        recommendations: List[Dict[str, Any]] = []
        
        # Track total covered weight
        total_weight_covered = 0.0
        total_required_weight = len(missing_skills)
        
        # Greedy set cover loop
        while uncovered_skills:
            # Find best subject
            best_subject = self.find_best_subject(
                subjects, uncovered_skills, selected_subjects
            )
            
            if best_subject is None:
                # No more subjects can cover remaining skills
                break
            
            # Add subject to selection
            selected_subjects.append(best_subject)
            
            # Calculate contribution
            marginal, penalty = self.calculate_marginal_contribution(
                best_subject, uncovered_skills, selected_subjects[:-1]
            )
            
            # Calculate covered skills and their weights
            subject_skills = set(best_subject.get("covered_skills", []))
            newly_covered = subject_skills & uncovered_skills
            
            # Get skill weights
            skill_weights = best_subject.get("skill_weights", {})
            covered_weight = sum(
                skill_weights.get(skill, 0.5) 
                for skill in newly_covered
            )
            
            # Update uncovered skills
            uncovered_skills = uncovered_skills - subject_skills
            total_weight_covered += covered_weight
            
            # Add to recommendations
            recommendations.append({
                "subject_name": best_subject.get("name", ""),
                "subject_code": best_subject.get("code", ""),
                "covered_skills": list(subject_skills),
                "marginal_contribution": round(marginal, 3),
                "redundancy_penalty": round(penalty, 3),
                "skills_added": list(newly_covered)
            })
        
        # Calculate total coverage
        total_coverage = (
            total_weight_covered / total_required_weight 
            if total_required_weight > 0 else 0.0
        )
        
        return {
            "selected_subjects": recommendations,
            "total_coverage": round(total_coverage, 3),
            "remaining_gaps": list(uncovered_skills)
        }
    
    def get_coverage_breakdown(
        self,
        selected_subject_names: List[str],
        role_key: str
    ) -> Dict[str, Any]:
        """
        Get detailed coverage breakdown for selected subjects.
        
        Args:
            selected_subject_names: List of subject names
            role_key: Target role key
            
        Returns:
            Dict with coverage details
        """
        # Get role profile
        role_profile = self._data_loader.get_role_profile(role_key)
        
        if not role_profile:
            return {
                "error": f"Role '{role_key}' not found"
            }
        
        # Get required skills
        required_skills = {
            s["skill"]: s["weightage"] 
            for s in role_profile.get("required_skills", [])
        }
        
        # Get selected subjects
        selected_subjects = []
        for name in selected_subject_names:
            subject = self._data_loader.get_subject_by_name(name)
            if subject:
                selected_subjects.append(subject)
        
        # Calculate coverage
        covered_skills = set()
        skill_sources: Dict[str, List[str]] = {}
        
        for subject in selected_subjects:
            for skill in subject.get("covered_skills", []):
                covered_skills.add(skill)
                if skill not in skill_sources:
                    skill_sources[skill] = []
                skill_sources[skill].append(subject.get("name", ""))
        
        # Calculate weighted coverage
        total_weight = sum(required_skills.values())
        covered_weight = sum(
            required_skills[skill] 
            for skill in covered_skills 
            if skill in required_skills
        )
        
        coverage_percent = (
            (covered_weight / total_weight * 100) 
            if total_weight > 0 else 0.0
        )
        
        # Build skill breakdown
        skill_coverage = []
        for skill, weight in required_skills.items():
            skill_coverage.append({
                "skill": skill,
                "covered": skill in covered_skills,
                "weightage": weight,
                "source_subjects": skill_sources.get(skill, [])
            })
        
        # Find remaining gaps
        remaining_gaps = [
            skill 
            for skill in required_skills.keys() 
            if skill not in covered_skills
        ]
        
        return {
            "updated_coverage_percent": round(coverage_percent, 2),
            "remaining_gaps": remaining_gaps,
            "skill_coverage_breakdown": skill_coverage
        }


# Create a global instance
_mece_engine: Optional[MECERecommendationEngine] = None


def get_mece_engine() -> MECERecommendationEngine:
    """
    Get the global MECE engine instance.
    
    Returns:
        The singleton MECERecommendationEngine instance
    """
    global _mece_engine
    if _mece_engine is None:
        _mece_engine = MECERecommendationEngine()
    return _mece_engine