"""
LLM Provider Abstraction.

This module defines the abstract base class for LLM providers,
allowing multiple backends (Gemini, OpenAI, Anthropic, Ollama) to be used
with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMProviderConfig(BaseModel):
    """Base configuration for LLM providers."""
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 2048


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    text: str
    raw_response: Any
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM implementations must inherit from this class and implement
    the required methods. This allows swapping between providers without
    changing the rest of the application.
    """
    
    def __init__(self, config: Optional[LLMProviderConfig] = None):
        """
        Initialize the provider with optional config.
        
        Args:
            config: Provider-specific configuration
        """
        self._config = config or LLMProviderConfig()
        self._initialized = False
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'gemini', 'openai')."""
        pass
    
    @property
    def model(self) -> str:
        """Get the configured model."""
        return self._config.model
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and configured.
        
        Returns:
            True if provider can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[LLMResponse]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override max tokens
            
        Returns:
            LLMResponse or None if failed
        """
        pass
    
    def parse_curriculum(
        self,
        curriculum_text: str,
        skill_taxonomy: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse curriculum and extract skills.
        
        Default implementation uses generic prompting. Providers
        can override for specialized behavior.
        
        Args:
            curriculum_text: Raw curriculum text
            skill_taxonomy: Optional skill taxonomy
            
        Returns:
            Dict with skills, subjects, proficiency_level or None
        """
        taxonomy_context = ""
        if skill_taxonomy:
            all_skills = []
            for category, skills in skill_taxonomy.items():
                all_skills.extend(skills.keys())
            taxonomy_context = f"\n\nKnown skills: {', '.join(all_skills)}"
        
        prompt = f"""Analyze this college curriculum and extract skills relevant for job placement.

CURRICULUM:
{curriculum_text}
{taxonomy_context}

Return JSON:
{{
    "skills": [{{"name": "skill", "proficiency": "basic/intermediate/advanced", "source": "course"}}],
    "subjects": ["list of subjects"],
    "proficiency_level": "overall level"
}}"""
        
        response = self.generate(prompt)
        if not response:
            return None
        
        try:
            import json
            parsed = json.loads(response.text)
            return parsed
        except (json.JSONDecodeError, AttributeError):
            return None
    
    def normalize_skill(
        self,
        raw_skill: str,
        known_skills: List[str]
    ) -> Optional[str]:
        """
        Normalize a skill to canonical form.
        
        Default implementation uses generic prompting.
        
        Args:
            raw_skill: Raw skill text
            known_skills: List of canonical skills
            
        Returns:
            Normalized skill name or None
        """
        prompt = f"""Map "{raw_skill}" to the best matching skill from this list:
{', '.join(known_skills)}

Return only the skill name, nothing else."""
        
        response = self.generate(prompt, temperature=0.3, max_tokens=50)
        if response:
            return response.text.strip()
        return None
    
    def generate_explanation(
        self,
        missing_skills: List[str],
        recommended_subjects: List[Dict],
        target_role: str
    ) -> Optional[str]:
        """
        Generate explanation for recommendations.
        
        Args:
            missing_skills: Skills lacking
            recommended_subjects: Recommended subjects with details
            target_role: Target job role
            
        Returns:
            Explanation text or None
        """
        subjects_text = "\n".join([
            f"- {s.get('subject_name', 'Unknown')}: covers {', '.join(s.get('covered_skills', []))}"
            for s in recommended_subjects
        ])
        
        prompt = f"""Explain why these subjects are recommended for becoming a {target_role}.

Missing skills: {', '.join(missing_skills)}

Recommended subjects:
{subjects_text}

Write 2-3 paragraphs explaining how these courses help close skill gaps."""
        
        response = self.generate(prompt, temperature=0.7, max_tokens=500)
        if response:
            return response.text.strip()
        return None
    
    def suggest_interview_topics(
        self,
        skills: List[str],
        role: str
    ) -> Optional[List[str]]:
        """
        Suggest interview topics based on skills.
        
        Args:
            skills: Skills to prepare for
            role: Target role
            
        Returns:
            List of topics or None
        """
        prompt = f"""For a {role} position, suggest 5-8 interview topics based on:
{', '.join(skills)}

Return as JSON array: ["topic1", "topic2", ...]"""
        
        response = self.generate(prompt, temperature=0.5, max_tokens=300)
        if not response:
            return None
        
        try:
            import json
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except (json.JSONDecodeError, AttributeError):
            return None