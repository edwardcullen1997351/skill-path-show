"""
Utilities package for Skill Path Show API.

This package provides utility functions for:
- Data loading (JSON files)
- NLP processing (text tokenization, keyword extraction)
- Skill normalization (synonym mapping)
- MECE algorithm (set cover for recommendations)
"""

from app.utils.data_loader import (
    DataLoader,
    get_data_loader
)

from app.utils.nlp_utils import (
    tokenize,
    extract_keywords,
    extract_phrases,
    clean_text,
    get_ngrams,
    detect_level,
    extract_subject_codes
)

from app.utils.skill_normalizer import (
    SkillNormalizer,
    get_skill_normalizer,
    normalize_skill,
    normalize_skills
)

from app.utils.mece_algorithm import (
    MECERecommendationEngine,
    get_mece_engine
)

from app.utils.similarity import (
    SkillSimilarity,
    get_skill_similarity,
    find_similar_skills,
    find_closest_skill
)

from app.utils.cache import (
    SimpleCache,
    get_role_cache,
    get_skill_cache,
    get_subjects_cache,
    get_cache_stats,
    cached
)

from app.utils.llm_service import (
    GeminiService,
    get_gemini_service,
    is_llm_available,
    LLMParserResponse
)

__all__ = [
    # Data loader
    "DataLoader",
    "get_data_loader",
    
    # NLP utilities
    "tokenize",
    "extract_keywords",
    "extract_phrases",
    "clean_text",
    "get_ngrams",
    "detect_level",
    "extract_subject_codes",
    
    # Skill normalizer
    "SkillNormalizer",
    "get_skill_normalizer",
    "normalize_skill",
    "normalize_skills",
    
    # MECE algorithm
    "MECERecommendationEngine",
    "get_mece_engine",
    
    # Similarity
    "SkillSimilarity",
    "get_skill_similarity",
    "find_similar_skills",
    "find_closest_skill",
    
    # Caching
    "SimpleCache",
    "get_role_cache",
    "get_skill_cache",
    "get_subjects_cache",
    "get_cache_stats",
    "cached",
    
    # LLM Service
    "GeminiService",
    "get_gemini_service",
    "is_llm_available",
    "LLMParserResponse"
]