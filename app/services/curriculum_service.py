"""
Curriculum processing service.

This service handles parsing curriculum text and extracting
skills from it using NLP and skill normalization.
"""

from typing import List, Dict, Any
from app.models.curriculum import (
    CurriculumInput,
    CurriculumOutput,
    ExtractedSkill
)
from app.utils.data_loader import get_data_loader
from app.utils.nlp_utils import (
    extract_keywords,
    extract_phrases,
    detect_level,
    extract_subject_codes,
    tokenize
)
from app.utils.skill_normalizer import get_skill_normalizer


class CurriculumService:
    """
    Service for processing curriculum data and extracting skills.
    """
    
    def __init__(self):
        """Initialize the curriculum service."""
        self._data_loader = get_data_loader()
        self._skill_normalizer = get_skill_normalizer()
    
    def parse_curriculum(self, input_data: CurriculumInput) -> CurriculumOutput:
        """
        Parse curriculum input and extract skills.
        
        Args:
            input_data: The curriculum input data
            
        Returns:
            CurriculumOutput with extracted subjects and skills
        """
        subjects: List[str] = []
        extracted_skills: List[ExtractedSkill] = []
        
        # Process text input
        if input_data.text:
            text_subjects, text_skills = self._process_text(input_data.text)
            subjects.extend(text_subjects)
            extracted_skills.extend(text_skills)
        
        # Process subject codes
        if input_data.subjects:
            code_subjects, code_skills = self._process_subject_codes(
                input_data.subjects
            )
            subjects.extend(code_subjects)
            extracted_skills.extend(code_skills)
        
        # Process raw JSON input
        if input_data.raw_json:
            json_subjects, json_skills = self._process_json(input_data.raw_json)
            subjects.extend(json_subjects)
            extracted_skills.extend(json_skills)
        
        # Determine overall skill proficiency
        skill_proficiency = self._determine_proficiency(extracted_skills)
        
        # Remove duplicates from subjects
        subjects = list(dict.fromkeys(subjects))
        
        return CurriculumOutput(
            subjects=subjects,
            extracted_skills=extracted_skills,
            skill_proficiency=skill_proficiency
        )
    
    def _process_text(self, text: str) -> tuple:
        """
        Process raw text input.
        
        Args:
            text: Raw curriculum text
            
        Returns:
            Tuple of (subjects, extracted_skills)
        """
        subjects: List[str] = []
        extracted_skills: List[ExtractedSkill] = []
        
        # Extract subject codes
        codes = extract_subject_codes(text)
        
        # Get subject names from codes
        for code in codes:
            subject = self._data_loader.get_subject_by_code(code)
            if subject and subject.get("name"):
                subjects.append(subject["name"])
                
                # Extract skills from subject
                for skill in subject.get("covered_skills", []):
                    extracted_skills.append(ExtractedSkill(
                        skill=skill,
                        proficiency=subject.get("level", "intermediate"),
                        source=subject["name"]
                    ))
        
        # Also extract skills directly from text
        keywords = extract_keywords(text)
        
        # Normalize skills from keywords
        for keyword in keywords:
            normalized = self._skill_normalizer.normalize(keyword)
            
            # Check if skill is already added
            existing = [s for s in extracted_skills if s.skill == normalized]
            if not existing:
                level = detect_level(keyword)
                extracted_skills.append(ExtractedSkill(
                    skill=normalized,
                    proficiency=level,
                    source="Text Analysis"
                ))
        
        # Also try to identify subjects from text
        all_subjects = self._data_loader.load_subjects_catalog()
        text_lower = text.lower()
        
        for subject in all_subjects:
            subject_name_lower = subject.get("name", "").lower()
            
            # Check if subject is mentioned in text
            if any(word in text_lower for word in subject_name_lower.split()[:2]):
                if subject.get("name") not in subjects:
                    subjects.append(subject.get("name", ""))
                    
                    # Add skills from this subject if not already added
                    for skill in subject.get("covered_skills", []):
                        if not any(s.skill == skill for s in extracted_skills):
                            extracted_skills.append(ExtractedSkill(
                                skill=skill,
                                proficiency=subject.get("level", "intermediate"),
                                source=subject["name"]
                            ))
        
        return subjects, extracted_skills
    
    def _process_subject_codes(
        self,
        codes: List[str]
    ) -> tuple:
        """
        Process subject codes list.
        
        Args:
            codes: List of subject codes (e.g., ['CS201', 'CS301'])
            
        Returns:
            Tuple of (subjects, extracted_skills)
        """
        subjects: List[str] = []
        extracted_skills: List[ExtractedSkill] = []
        
        for code in codes:
            subject = self._data_loader.get_subject_by_code(code)
            
            if subject:
                if subject.get("name"):
                    subjects.append(subject["name"])
                
                # Extract skills from subject
                for skill in subject.get("covered_skills", []):
                    # Check if skill already exists
                    if not any(s.skill == skill for s in extracted_skills):
                        extracted_skills.append(ExtractedSkill(
                            skill=skill,
                            proficiency=subject.get("level", "intermediate"),
                            source=subject.get("name", code)
                        ))
        
        return subjects, extracted_skills
    
    def _process_json(self, json_data: Dict) -> tuple:
        """
        Process structured JSON curriculum data.
        
        Args:
            json_data: Structured JSON data
            
        Returns:
            Tuple of (subjects, extracted_skills)
        """
        subjects: List[str] = []
        extracted_skills: List[ExtractedSkill] = []
        
        # Handle different JSON structures
        if "subjects" in json_data:
            for subj in json_data["subjects"]:
                if isinstance(subj, dict):
                    name = subj.get("name", subj.get("code", ""))
                    subjects.append(name)
                    
                    for skill in subj.get("skills", []):
                        if not any(s.skill == skill for s in extracted_skills):
                            extracted_skills.append(ExtractedSkill(
                                skill=skill,
                                proficiency=subj.get("level", "intermediate"),
                                source=name
                            ))
        
        elif "courses" in json_data:
            for course in json_data["courses"]:
                if isinstance(course, dict):
                    name = course.get("name", course.get("code", ""))
                    subjects.append(name)
                    
                    for skill in course.get("skills", []):
                        if not any(s.skill == skill for s in extracted_skills):
                            extracted_skills.append(ExtractedSkill(
                                skill=skill,
                                proficiency=course.get("level", "intermediate"),
                                source=name
                            ))
        
        return subjects, extracted_skills
    
    def _determine_proficiency(
        self,
        skills: List[ExtractedSkill]
    ) -> str:
        """
        Determine overall skill proficiency level.
        
        Args:
            skills: List of extracted skills
            
        Returns:
            Proficiency level: 'basic', 'intermediate', or 'advanced'
        """
        if not skills:
            return "basic"
        
        # Count proficiency levels
        level_counts = {"basic": 0, "intermediate": 0, "advanced": 0}
        
        for skill in skills:
            if skill.proficiency in level_counts:
                level_counts[skill.proficiency] += 1
        
        # Return most common level
        return max(level_counts, key=level_counts.get)


# Create a global instance
_curriculum_service: Any = None


def get_curriculum_service() -> CurriculumService:
    """
    Get the global curriculum service instance.
    
    Returns:
        The singleton CurriculumService instance
    """
    global _curriculum_service
    if _curriculum_service is None:
        _curriculum_service = CurriculumService()
    return _curriculum_service