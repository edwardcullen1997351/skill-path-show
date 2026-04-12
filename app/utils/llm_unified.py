"""
Unified LLM Service.

This module provides a unified interface for all LLM providers,
abstracting away the specific implementation details.
"""

from typing import Optional, Dict, Any, List
from app.providers import get_provider, create_provider, get_provider_registry
from app.providers.base import LLMProvider, LLMResponse


class LLMService:
    """
    Unified service for LLM operations.
    
    This class wraps individual providers and provides a consistent
    interface for all LLM operations.
    """
    
    def __init__(self, default_provider: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            default_provider: Default provider name
        """
        self._default_provider = default_provider
        self._current_provider: Optional[LLMProvider] = None
    
    def set_provider(self, provider_name: str) -> bool:
        """
        Set the current provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if successful, False otherwise
        """
        provider = get_provider(provider_name)
        if provider and provider.is_available():
            self._current_provider = provider
            self._default_provider = provider_name
            return True
        return False
    
    def get_current_provider(self) -> Optional[LLMProvider]:
        """
        Get the current provider.
        
        Returns:
            Current provider or default
        """
        if self._current_provider:
            return self._current_provider
        
        if self._default_provider:
            return get_provider(self._default_provider)
        
        return get_provider()
    
    def parse_curriculum(
        self,
        curriculum_text: str,
        skill_taxonomy: Optional[Dict] = None,
        provider: Optional[str] = None,
        use_fine_tuned: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Parse curriculum using LLM.
        
        Args:
            curriculum_text: Raw curriculum text
            skill_taxonomy: Optional skill taxonomy
            provider: Optional provider override
            use_fine_tuned: Use domain-optimized prompts (few-shot learning)
            
        Returns:
            Dict with skills, subjects, proficiency_level or None
        """
        p = get_provider(provider) if provider else self.get_current_provider()
        if not p:
            return None
        
        if use_fine_tuned:
            from app.prompts import get_prompt_templates
            templates = get_prompt_templates()
            prompt = templates.get_curriculum_prompt(skill_taxonomy, use_few_shot=True)
            prompt = prompt.format(curriculum_text=curriculum_text)
            
            response = p.generate(prompt, temperature=0.3, max_tokens=2048)
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
        
        return p.parse_curriculum(curriculum_text, skill_taxonomy)
    
    def normalize_skill(
        self,
        raw_skill: str,
        known_skills: List[str],
        provider: Optional[str] = None,
        use_fine_tuned: bool = False
    ) -> Optional[str]:
        """
        Normalize a skill to canonical form.
        
        Args:
            raw_skill: Raw skill text
            known_skills: List of known skills
            provider: Optional provider override
            use_fine_tuned: Use domain-optimized prompts
            
        Returns:
            Normalized skill or None
        """
        p = get_provider(provider) if provider else self.get_current_provider()
        if not p:
            return None
        
        if use_fine_tuned:
            from app.prompts import get_prompt_templates
            templates = get_prompt_templates()
            prompt = templates.get_skill_normalization_prompt(known_skills, use_few_shot=True)
            prompt = prompt.format(raw_skill=raw_skill)
            
            response = p.generate(prompt, temperature=0.2, max_tokens=100)
            if response:
                return response.text.strip()
            return None
        
        return p.normalize_skill(raw_skill, known_skills)
    
    def generate_explanation(
        self,
        missing_skills: List[str],
        recommended_subjects: List[Dict],
        target_role: str,
        provider: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate explanation for recommendations.
        
        Args:
            missing_skills: Skills lacking
            recommended_subjects: Recommended subjects
            target_role: Target role
            provider: Optional provider override
            
        Returns:
            Explanation or None
        """
        p = get_provider(provider) if provider else self.get_current_provider()
        if not p:
            return None
        
        return p.generate_explanation(missing_skills, recommended_subjects, target_role)
    
    def suggest_interview_topics(
        self,
        skills: List[str],
        role: str,
        provider: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        Suggest interview topics.
        
        Args:
            skills: Skills to prepare for
            role: Target role
            provider: Optional provider override
            
        Returns:
            List of topics or None
        """
        p = get_provider(provider) if provider else self.get_current_provider()
        if not p:
            return None
        
        return p.suggest_interview_topics(skills, role)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """
        Generate raw LLM response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            provider: Optional provider override
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse or None
        """
        p = get_provider(provider) if provider else self.get_current_provider()
        if not p:
            return None
        
        return p.generate(prompt, system_prompt, **kwargs)
    
    def compare_providers(
        self,
        prompt: str,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Optional[LLMResponse]]:
        """
        Compare outputs from multiple providers.
        
        Args:
            prompt: Prompt to send
            providers: List of providers to compare (default: all available)
            
        Returns:
            Dict of provider name to response
        """
        if providers is None:
            registry = get_provider_registry()
            providers = [name for name in registry._providers.keys()]
        
        results = {}
        for name in providers:
            provider = get_provider(name)
            if provider and provider.is_available():
                results[name] = provider.generate(prompt)
            else:
                results[name] = None
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all providers.
        
        Returns:
            Dict with provider status info
        """
        registry = get_provider_registry()
        providers = registry.list_providers()
        
        default = self._default_provider or registry._default_provider
        
        return {
            "providers": providers,
            "default_provider": default,
            "current_provider": self._default_provider
        }


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service