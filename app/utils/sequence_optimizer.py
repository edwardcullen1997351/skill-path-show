"""
Sequence Optimizer for Learning Path Generation.

This module provides functionality to:
- Derive prerequisites from subject levels and covered skills
- Perform topological sorting for optimal learning order
- Split recommendations into semesters based on time constraints
"""

from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict, deque
from app.utils.data_loader import get_data_loader


class SequenceOptimizer:
    """Optimizer for learning sequence based on dependencies and constraints."""
    
    LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
    
    def __init__(self):
        """Initialize the sequence optimizer."""
        self._data_loader = get_data_loader()
    
    def derive_prerequisites(self, subjects: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Derive prerequisites from subject levels and skill dependencies.
        
        Args:
            subjects: List of subject dictionaries with level and covered_skills
            
        Returns:
            Dict mapping subject code to list of prerequisite codes
        """
        subject_by_code = {s.get("code"): s for s in subjects}
        prerequisites: Dict[str, List[str]] = defaultdict(list)
        
        for subject in subjects:
            code = subject.get("code", "")
            level = subject.get("level", "beginner")
            skills = set(subject.get("covered_skills", []))
            
            for other in subjects:
                if other.get("code") == code:
                    continue
                    
                other_level = other.get("level", "beginner")
                other_skills = set(other.get("covered_skills", []))
                
                if self.LEVEL_ORDER.get(other_level, 0) < self.LEVEL_ORDER.get(level, 0):
                    if skills & other_skills:
                        if other.get("code") not in prerequisites[code]:
                            prerequisites[code].append(other.get("code", ""))
        
        return dict(prerequisites)
    
    def build_dependency_graph(
        self,
        subjects: List[Dict[str, Any]],
        prerequisites: Dict[str, List[str]]
    ) -> Dict[str, Set[str]]:
        """
        Build a dependency graph for topological sorting.
        
        Args:
            subjects: List of subjects
            prerequisites: Pre-computed prerequisites
            
        Returns:
            Adjacency list representation of dependency graph
        """
        graph = defaultdict(set)
        in_degree = defaultdict(int)
        
        subject_codes = {s.get("code") for s in subjects}
        
        for subject in subjects:
            code = subject.get("code", "")
            in_degree[code] = 0
            graph[code] = set()
        
        for code, prereqs in prerequisites.items():
            if code in subject_codes:
                for prereq in prereqs:
                    if prereq in subject_codes:
                        graph[prereq].add(code)
                        in_degree[code] += 1
        
        return dict(graph), dict(in_degree)
    
    def topological_sort(
        self,
        subjects: List[Dict[str, Any]],
        prerequisites: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform topological sort to order subjects by dependencies.
        
        Uses Kahn's algorithm for topological sorting.
        
        Args:
            subjects: List of subjects to order
            prerequisites: Optional pre-computed prerequisites
            
        Returns:
            List of subjects in dependency-respecting order
        """
        if prerequisites is None:
            prerequisites = self.derive_prerequisites(subjects)
        
        graph, in_degree = self.build_dependency_graph(subjects, prerequisites)
        
        queue = deque()
        for code, degree in in_degree.items():
            if degree == 0:
                queue.append(code)
        
        ordered = []
        subject_map = {s.get("code"): s for s in subjects}
        
        while queue:
            current = queue.popleft()
            if current in subject_map:
                ordered.append(subject_map[current])
            
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        remaining = [subject_map[code] for code in in_degree if in_degree[code] > 0 and code in subject_map]
        ordered.extend(remaining)
        
        return ordered
    
    def estimate_hours(self, subject: Dict[str, Any]) -> int:
        """
        Estimate hours required for a subject.
        
        Args:
            subject: Subject dictionary with credits
            
        Returns:
            Estimated hours (credits * 10)
        """
        credits = subject.get("credits", 3)
        return credits * 10
    
    def split_into_semesters(
        self,
        subjects: List[Dict[str, Any]],
        weekly_hours: int = 10,
        weeks_per_term: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Split subjects into semesters based on time constraints.
        
        Args:
            subjects: Ordered list of subjects
            weekly_hours: Available hours per week
            weeks_per_term: Number of weeks per semester/term
            
        Returns:
            List of semester dictionaries with subjects and totals
        """
        hours_per_term = weekly_hours * weeks_per_term
        semesters = []
        current_semester = {"semester": 1, "subjects": [], "total_hours": 0}
        
        for subject in subjects:
            subject_hours = self.estimate_hours(subject)
            
            if current_semester["total_hours"] + subject_hours > hours_per_term:
                if current_semester["subjects"]:
                    current_semester["total_credits"] = sum(
                        s.get("credits", 3) for s in current_semester["subjects"]
                    )
                    semesters.append(current_semester)
                
                current_semester = {
                    "semester": len(semesters) + 1,
                    "subjects": [],
                    "total_hours": 0
                }
            
            current_semester["subjects"].append({
                "subject_name": subject.get("name", ""),
                "subject_code": subject.get("code", ""),
                "estimated_hours": subject_hours,
                "credits": subject.get("credits", 3),
                "level": subject.get("level", ""),
                "covered_skills": subject.get("covered_skills", [])
            })
            current_semester["total_hours"] += subject_hours
        
        if current_semester["subjects"]:
            current_semester["total_credits"] = sum(
                s.get("credits", 3) for s in current_semester["subjects"]
            )
            semesters.append(current_semester)
        
        return semesters
    
    def calculate_total_duration(
        self,
        semesters: List[Dict[str, Any]],
        weeks_per_term: int = 8
    ) -> Dict[str, Any]:
        """
        Calculate total learning path duration.
        
        Args:
            semesters: List of semesters
            weeks_per_term: Weeks per term
            
        Returns:
            Dict with duration information
        """
        total_weeks = len(semesters) * weeks_per_term
        total_months = round(total_weeks / 4)
        
        total_hours = sum(s.get("total_hours", 0) for s in semesters)
        total_credits = sum(s.get("total_credits", 0) for s in semesters)
        
        return {
            "total_semesters": len(semesters),
            "total_weeks": total_weeks,
            "total_months": total_months,
            "total_hours": total_hours,
            "total_credits": total_credits
        }


_optimizer: Optional[SequenceOptimizer] = None


def get_sequence_optimizer() -> SequenceOptimizer:
    """Get the global sequence optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = SequenceOptimizer()
    return _optimizer