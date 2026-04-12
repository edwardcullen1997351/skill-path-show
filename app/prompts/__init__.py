"""
Domain-Specific Prompt Templates.

This module contains optimized prompts for curriculum parsing,
skill extraction, and recommendations using few-shot learning
techniques for improved accuracy.
"""

import json
import os
from typing import Dict, List, Any, Optional


class PromptTemplates:
    """Collection of domain-specific prompt templates."""
    
    def __init__(self):
        """Initialize with example data."""
        self._examples = self._load_examples()
    
    def _load_examples(self) -> Dict[str, Any]:
        """Load fine-tuning examples from data file."""
        examples_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "data", 
            "fine_tuning_examples.json"
        )
        
        try:
            with open(examples_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"curriculum_parsing": [], "skill_normalization": []}
    
    def get_curriculum_prompt(
        self,
        skill_taxonomy: Optional[Dict] = None,
        use_few_shot: bool = True
    ) -> str:
        """
        Get curriculum parsing prompt with optional few-shot examples.
        
        Args:
            skill_taxonomy: Optional skill taxonomy for reference
            use_few_shot: Whether to include few-shot examples
            
        Returns:
            Formatted prompt string
        """
        taxonomy_context = ""
        if skill_taxonomy:
            all_skills = []
            for category, skills in skill_taxonomy.items():
                all_skills.extend(skills.keys())
            taxonomy_context = f"\n\nPrefer these canonical skills: {', '.join(all_skills[:50])}"
        
        base_prompt = """You are a curriculum analyst specializing in extracting skills from college course descriptions.
Analyze the curriculum and extract relevant technical skills for job placement.
"""
        
        if use_few_shot and self._examples.get("curriculum_parsing"):
            examples = self._examples["curriculum_parsing"][:2]
            few_shot = "\n\nExamples:\n"
            for ex in examples:
                few_shot += f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'])}\n"
            
            base_prompt += few_shot
        
        base_prompt += f"""
Now analyze this curriculum:

CURRICULUM:
{{curriculum_text}}{taxonomy_context}

Return JSON with this exact structure:
{{
    "skills": [{{"name": "skill_name", "proficiency": "basic/intermediate/advanced", "source": "course_name"}}],
    "subjects": ["list of subject names"],
    "proficiency_level": "overall proficiency (basic/intermediate/advanced)"
}}

Extract as many skills as possible from the courses. Map to canonical skill names."""
        
        return base_prompt
    
    def get_skill_normalization_prompt(
        self,
        known_skills: List[str],
        use_few_shot: bool = True
    ) -> str:
        """
        Get skill normalization prompt.
        
        Args:
            known_skills: List of known canonical skills
            use_few_shot: Whether to include few-shot examples
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""You are a skill normalizer. Map raw skill names to their canonical forms."""
        
        if use_few_shot and self._examples.get("skill_normalization"):
            examples = self._examples["skill_normalization"][:3]
            few_shot = "\n\nExamples:\n"
            for ex in examples:
                few_shot += f'Input: "{ex["input"]}"\nOutput: "{ex["output"]}"\n'
            
            base_prompt += few_shot
        
        base_prompt += f"""
Now normalize this skill:

Known canonical skills: {{', '.join(known_skills)}}

Raw skill: "{{raw_skill}}"

Return only the canonical skill name in lowercase with underscores. If no match, return the original in lowercase."""
        
        return base_prompt
    
    def get_recommendation_explanation_prompt(self) -> str:
        """
        Get recommendation explanation prompt.
        
        Returns:
            Formatted prompt string
        """
        return """You are a career advisor explaining learning path recommendations.

Generate a 2-3 paragraph explanation for why these subjects are recommended.
Make it encouraging and specific to the target role.

Missing skills: {missing_skills}

Recommended subjects:
{subjects_text}

Target role: {target_role}

Write a helpful explanation."""
    
    def get_interview_topics_prompt(self) -> str:
        """
        Get interview topics generation prompt.
        
        Returns:
            Formatted prompt string
        """
        return """For a {role} position, suggest 5-8 technical interview topics.

Consider these skills: {skills}

Return as JSON array: ["topic1", "topic2", ...]"""
    
    def get_system_prompt(self, task: str = "general") -> str:
        """
        Get task-specific system prompt.
        
        Args:
            task: Type of task (general, curriculum, skill, recommendation)
            
        Returns:
            System prompt string
        """
        prompts = {
            "general": "You are a helpful career and education advisor AI.",
            "curriculum": "You are a curriculum analyst specializing in extracting technical skills from course descriptions.",
            "skill": "You are a skill normalization expert. Map raw skill names to canonical forms.",
            "recommendation": "You are a helpful career advisor explaining learning recommendations."
        }
        return prompts.get(task, prompts["general"])


_templates: Optional[PromptTemplates] = None


def get_prompt_templates() -> PromptTemplates:
    """Get the global prompt templates instance."""
    global _templates
    if _templates is None:
        _templates = PromptTemplates()
    return _templates