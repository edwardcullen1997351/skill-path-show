"""
LLM Service using Google Gemini.

This module provides integration with Google Gemini for:
- Curriculum parsing and skill extraction
- Skill normalization
- Personalized recommendations
"""

import os
import json
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class GeminiConfig(BaseModel):
    """Configuration for Gemini API."""
    api_key: str = ""
    model: str = "gemini-1.5-flash"
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMParserResponse(BaseModel):
    """Response from LLM curriculum parser."""
    skills: List[Dict[str, Any]]
    subjects: List[str]
    proficiency_level: str
    raw_response: str


class GeminiService:
    """
    Service for interacting with Google Gemini LLM.
    
    Provides methods for:
    - Parsing curriculum text to extract skills
    - Normalizing skill names
    - Generating personalized recommendations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini service.
        
        Args:
            api_key: Google API key (will use env var if not provided)
        """
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._config = GeminiConfig(api_key=self._api_key)
        self._client = None
        self._initialized = False
    
    def _initialize(self) -> bool:
        """
        Initialize the Gemini client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized or not self._api_key:
            return self._api_key != ""
        
        try:
            import genai
            genai.configure(api_key=self._api_key)
            self._client = genai
            self._initialized = True
            return True
        except ImportError:
            print("Warning: genai not installed")
            return False
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if Gemini is available.
        
        Returns:
            True if API key is set and client initialized
        """
        return self._initialize()
    
    def parse_curriculum_with_llm(
        self,
        curriculum_text: str,
        skill_taxonomy: Optional[Dict] = None
    ) -> Optional[LLMParserResponse]:
        """
        Use Gemini to parse curriculum and extract skills.
        
        Args:
            curriculum_text: Raw curriculum text
            skill_taxonomy: Optional skill taxonomy for reference
            
        Returns:
            LLMParserResponse with extracted skills or None
        """
        if not self.is_available():
            return None
        
        # Build the prompt
        taxonomy_context = ""
        if skill_taxonomy:
            # Flatten taxonomy for context
            all_skills = []
            for category, skills in skill_taxonomy.items():
                all_skills.extend(skills.keys())
            taxonomy_context = f"\n\nKnown skills (use these canonical names when possible): {', '.join(all_skills)}"
        
        prompt = f"""You are a career and education advisor. Analyze the following college curriculum and extract skills that would be relevant for job placement.

CURRICULUM TEXT:
{curriculum_text}
{taxonomy_context}

Your response should be in JSON format with this structure:
{{
    "skills": [
        {{"name": "skill_name", "proficiency": "basic/intermediate/advanced", "source": "course_or_subject"}}
    ],
    "subjects": ["list of identified subjects"],
    "proficiency_level": "overall proficiency (basic/intermediate/advanced)"
}}

Extract as many relevant skills as possible. Map skills to their canonical names if you know them.
Focus on technical skills, tools, frameworks, and domain knowledge.
"""
        
        try:
            model = self._client.GenerativeModel(self._config.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": self._config.temperature,
                    "max_output_tokens": self._config.max_tokens,
                }
            )
            
            # Parse the response
            response_text = response.text
            
            # Try to extract JSON from response
            # Handle markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            parsed = json.loads(response_text.strip())
            
            return LLMParserResponse(
                skills=parsed.get("skills", []),
                subjects=parsed.get("subjects", []),
                proficiency_level=parsed.get("proficiency_level", "intermediate"),
                raw_response=response.text
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            return None
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
    
    def normalize_skill_with_llm(
        self,
        raw_skill: str,
        known_skills: List[str]
    ) -> Optional[str]:
        """
        Use Gemini to normalize a skill to canonical form.
        
        Args:
            raw_skill: Raw skill text
            known_skills: List of known/canonical skills
            
        Returns:
            Normalized skill name or None
        """
        if not self.is_available():
            return None
        
        prompt = f"""Given the raw skill term: "{raw_skill}"

And the following list of known/canonical skills:
{', '.join(known_skills)}

Return the SINGLE best matching canonical skill name from the list above. 
If none match well, return the original skill with proper formatting (lowercase, underscores).

Just return the skill name, nothing else.
"""
        
        try:
            model = self._client.GenerativeModel(self._config.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temp for more deterministic output
                    "max_output_tokens": 100,
                }
            )
            
            normalized = response.text.strip()
            return normalized if normalized else raw_skill
        except Exception as e:
            print(f"Error normalizing skill with LLM: {e}")
            return None
    
    def generate_recommendation_explanation(
        self,
        missing_skills: List[str],
        recommended_subjects: List[Dict],
        target_role: str
    ) -> Optional[str]:
        """
        Generate a natural language explanation for recommendations.
        
        Args:
            missing_skills: List of skills lacking
            recommended_subjects: List of recommended subjects with details
            target_role: Target job role
            
        Returns:
            Explanation text or None
        """
        if not self.is_available():
            return None
        
        subjects_text = "\n".join([
            f"- {s.get('subject_name', 'Unknown')}: covers {', '.join(s.get('covered_skills', []))}"
            for s in recommended_subjects
        ])
        
        prompt = f"""You are a career advisor. Explain why these subjects are recommended for someone wanting to become a {target_role}.

Missing skills: {', '.join(missing_skills)}

Recommended subjects:
{subjects_text}

Write a brief, encouraging explanation (2-3 paragraphs) about how taking these courses will help close the skill gaps and prepare for the role.
"""
        
        try:
            model = self._client.GenerativeModel(self._config.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error generating explanation with LLM: {e}")
            return None
    
    def suggest_interview_topics(
        self,
        skills: List[str],
        role: str
    ) -> Optional[List[str]]:
        """
        Suggest interview preparation topics based on skills.
        
        Args:
            skills: List of skills to prepare for
            role: Target role
            
        Returns:
            List of interview topics or None
        """
        if not self.is_available():
            return None
        
        prompt = f"""For a {role} position, suggest 5-8 technical interview preparation topics based on these skills:
{', '.join(skills)}

Return as a JSON array of strings, e.g.:
["Topic 1", "Topic 2", ...]
"""
        
        try:
            model = self._client.GenerativeModel(self._config.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,
                    "max_output_tokens": 300,
                }
            )
            
            # Parse JSON array
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            return json.loads(response_text.strip())
        except Exception as e:
            print(f"Error generating interview topics: {e}")
            return None


# Global instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service(api_key: Optional[str] = None) -> GeminiService:
    """
    Get the global Gemini service instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        GeminiService instance
    """
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService(api_key=api_key)
    return _gemini_service


def is_llm_available() -> bool:
    """
    Check if LLM integration is available.
    
    Returns:
        True if API key is configured
    """
    return get_gemini_service().is_available()