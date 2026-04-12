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
_mece_extended: Optional["MECEExtended"] = None


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


class MECEExtended:
    """
    MECE++ - Extended MECE Algorithm with cost and dependency constraints.
    
    Enhancements over basic MECE:
    - Budget constraints (max hours/credits per term)
    - Level-based prerequisites
    - Multi-term optimization
    - Dependency validation
    """
    
    LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
    
    def __init__(self):
        """Initialize MECE++ with data loader."""
        self._data_loader = get_data_loader()
        self._base_engine = MECERecommendationEngine()
    
    def _get_subject_cost(self, subject: Dict[str, Any]) -> Tuple[int, int]:
        """
        Get cost (hours, credits) for a subject.
        
        Args:
            subject: Subject dictionary
            
        Returns:
            Tuple of (hours, credits)
        """
        credits = subject.get("credits", 3)
        hours = credits * 10
        return hours, credits
    
    def _get_prerequisites(self, subject: Dict[str, Any], all_subjects: List[Dict[str, Any]]) -> List[str]:
        """
        Get prerequisites for a subject based on level.
        
        Args:
            subject: Subject to get prerequisites for
            all_subjects: All available subjects
            
        Returns:
            List of prerequisite subject codes
        """
        level = subject.get("level", "beginner")
        skills = set(subject.get("covered_skills", []))
        prereqs = []
        
        for other in all_subjects:
            if other.get("code") == subject.get("code"):
                continue
            other_level = other.get("level", "beginner")
            if self.LEVEL_ORDER.get(other_level, 0) < self.LEVEL_ORDER.get(level, 0):
                other_skills = set(other.get("covered_skills", []))
                if skills & other_skills:
                    prereqs.append(other.get("code", ""))
        
        return prereqs
    
    def _validate_dependencies(
        self,
        selected: List[Dict[str, Any]],
        all_subjects: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all prerequisites are satisfied.
        
        Args:
            selected: Selected subjects
            all_subjects: All available subjects
            
        Returns:
            Tuple of (is_valid, missing_prerequisites)
        """
        selected_codes = {s.get("code") for s in selected}
        missing = []
        
        for subject in selected:
            prereqs = self._get_prerequisites(subject, all_subjects)
            for prereq in prereqs:
                if prereq not in selected_codes:
                    missing.append(f"{subject.get('code')} requires {prereq}")
        
        return len(missing) == 0, missing
    
    def _add_missing_prerequisites(
        self,
        subjects: List[Dict[str, Any]],
        all_subjects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Add missing prerequisite subjects.
        
        Args:
            subjects: Selected subjects
            all_subjects: All available subjects
            
        Returns:
            Extended list including prerequisites
        """
        all_codes = {s.get("code") for s in all_subjects}
        selected_codes = {s.get("code") for s in subjects}
        extended = list(subjects)
        
        for subject in subjects:
            prereqs = self._get_prerequisites(subject, all_subjects)
            for prereq in prereqs:
                if prereq in all_codes and prereq not in selected_codes:
                    prereq_subject = next((s for s in all_subjects if s.get("code") == prereq), None)
                    if prereq_subject and prereq_subject not in extended:
                        extended.append(prereq_subject)
        
        return extended
    
    def generate_learning_plan(
        self,
        missing_skills: List[str],
        weekly_hours: int = 10,
        max_credits_per_term: int = 9,
        weeks_per_term: int = 8,
        include_prerequisites: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a learning plan with cost and dependency constraints.
        
        Args:
            missing_skills: Skills that need coverage
            weekly_hours: Available hours per week
            max_credits_per_term: Maximum credits per term
            weeks_per_term: Number of weeks per term
            include_prerequisites: Whether to include prerequisites
            
        Returns:
            Learning plan with subjects organized by term
        """
        all_subjects = self._data_loader.load_subjects_catalog()
        
        base_result = self._base_engine.generate_recommendations(missing_skills)
        selected_subjects = base_result.get("selected_subjects", [])
        
        if not selected_subjects:
            return {
                "learning_path": [],
                "total_coverage": 0,
                "remaining_gaps": missing_skills
            }
        
        subject_map = {s.get("subject_code"): s for s in selected_subjects}
        subjects_to_order = [self._find_subject(s.get("subject_code"), all_subjects) for s in selected_subjects]
        subjects_to_order = [s for s in subjects_to_order if s]
        
        if include_prerequisites:
            subjects_to_order = self._add_missing_prerequisites(subjects_to_order, all_subjects)
        
        from app.utils.sequence_optimizer import get_sequence_optimizer
        optimizer = get_sequence_optimizer()
        
        prereqs = optimizer.derive_prerequisites(subjects_to_order)
        ordered_subjects = optimizer.topological_sort(subjects_to_order, prereqs)
        
        hours_per_term = weekly_hours * weeks_per_term
        terms = []
        current_term = {"term": 1, "subjects": [], "total_hours": 0, "total_credits": 0}
        
        for subject in ordered_subjects:
            hours, credits = self._get_subject_cost(subject)
            
            if current_term["total_credits"] + credits > max_credits_per_term:
                if current_term["subjects"]:
                    terms.append(current_term)
                current_term = {"term": len(terms) + 1, "subjects": [], "total_hours": 0, "total_credits": 0}
            
            current_term["subjects"].append({
                "subject_code": subject.get("code", ""),
                "subject_name": subject.get("name", ""),
                "covered_skills": subject.get("covered_skills", []),
                "level": subject.get("level", ""),
                "credits": credits,
                "estimated_hours": hours
            })
            current_term["total_hours"] += hours
            current_term["total_credits"] += credits
        
        if current_term["subjects"]:
            terms.append(current_term)
        
        total_hours = sum(t["total_hours"] for t in terms)
        total_credits = sum(t["total_credits"] for t in terms)
        total_weeks = len(terms) * weeks_per_term
        
        covered_skills = set()
        for subject in subjects_to_order:
            covered_skills.update(subject.get("covered_skills", []))
        
        coverage = len(covered_skills & set(missing_skills)) / len(missing_skills) if missing_skills else 0
        
        remaining_skills = [s for s in missing_skills if s not in covered_skills]
        
        return {
            "learning_path": terms,
            "total_coverage": round(coverage, 3),
            "remaining_gaps": remaining_skills,
            "summary": {
                "total_terms": len(terms),
                "total_weeks": total_weeks,
                "total_months": round(total_weeks / 4),
                "total_hours": total_hours,
                "total_credits": total_credits,
                "weekly_hours": weekly_hours
            }
        }
    
    def _find_subject(self, code: str, subjects: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find a subject by code."""
        for s in subjects:
            if s.get("code") == code:
                return s
        return None


def get_mece_extended() -> MECEExtended:
    """Get the global MECE++ instance."""
    global _mece_extended
    if _mece_extended is None:
        _mece_extended = MECEExtended()
    return _mece_extended