"""
Similarity and matching router.

This router provides endpoints for finding similar skills
using cosine similarity.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from app.utils.similarity import get_skill_similarity
from app.utils.data_loader import get_data_loader

router = APIRouter()


@router.post(
    "/similar-skills",
    summary="Find Similar Skills",
    description="""
    Find skills similar to a target skill using cosine similarity.
    
    Uses a bag-of-words approach with character n-grams for
    embedding-like matching even when skills aren't exact matches.
    """,
    tags=["Similarity"]
)
async def find_similar_skills(
    target_skill: str,
    threshold: float = 0.3,
    top_k: int = 5
):
    """
    Find skills similar to the target skill.
    
    Args:
        target_skill: Skill to find matches for
        threshold: Minimum similarity score (0-1)
        top_k: Maximum number of results
        
    Returns:
        List of similar skills with scores
    """
    similarity = get_skill_similarity()
    data_loader = get_data_loader()
    
    # Get all known skills from taxonomy
    taxonomy = data_loader.load_skills_taxonomy()
    all_skills = []
    
    for category, skills in taxonomy.items():
        all_skills.extend(skills.keys())
    
    # Also add skills from role profiles
    roles = data_loader.load_role_profiles()
    for role_key, role_data in roles.items():
        for skill_data in role_data.get("required_skills", []):
            if skill_data["skill"] not in all_skills:
                all_skills.append(skill_data["skill"])
    
    # Find similar skills
    similar = similarity.find_similar_skills(
        target_skill,
        all_skills,
        threshold=threshold,
        top_k=top_k
    )
    
    return {
        "target_skill": target_skill,
        "similar_skills": [
            {"skill": skill, "similarity": round(score, 3)}
            for skill, score in similar
        ],
        "count": len(similar)
    }


@router.get(
    "/skill-similarity-matrix",
    summary="Get Similarity Matrix",
    description="""
    Get pairwise similarity between all known skills.
    
    Useful for understanding skill relationships.
    """,
    tags=["Similarity"]
)
async def get_similarity_matrix(min_similarity: float = 0.5):
    """
    Get similarity matrix for all skills.
    
    Args:
        min_similarity: Minimum similarity to include
        
    Returns:
        Dict of skill pairs and their similarity scores
    """
    similarity = get_skill_similarity()
    data_loader = get_data_loader()
    
    # Get all skills
    taxonomy = data_loader.load_skills_taxonomy()
    all_skills = set()
    
    for category, skills in taxonomy.items():
        all_skills.update(skills.keys())
    
    # Get matrix
    matrix = similarity.get_skill_similarity_matrix(list(all_skills))
    
    # Filter by threshold
    filtered = {
        f"{k[0]} -> {k[1]}": round(v, 3)
        for k, v in matrix.items()
        if v >= min_similarity
    }
    
    return {
        "similarity_matrix": filtered,
        "total_pairs": len(filtered)
    }


@router.post(
    "/closest-match",
    summary="Find Closest Match",
    description="""
    Find the closest matching skill from a list of options.
    """,
    tags=["Similarity"]
)
async def find_closest_match(query: str, options: List[str]):
    """
    Find closest matching skill.
    
    Args:
        query: Query string
        options: List of possible matches
        
    Returns:
        Best match with similarity score
    """
    similarity = get_skill_similarity()
    
    result = similarity.find_closest_match(query, options)
    
    if result:
        return {
            "query": query,
            "best_match": result[0],
            "similarity": round(result[1], 3),
            "found": True
        }
    
    return {
        "query": query,
        "best_match": None,
        "similarity": 0.0,
        "found": False
    }