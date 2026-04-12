"""
Similarity and matching router.

This router provides endpoints for:
- Semantic skill matching using embeddings
- N-gram similarity (fallback)
- Skill ontology navigation
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.utils.similarity import get_skill_similarity, is_semantic_matching_available
from app.utils.data_loader import get_data_loader
from app.utils.skill_ontology import get_skill_ontology, get_skill_hierarchy, get_related_skills
from app.utils.embeddings import get_skills_index, rebuild_skills_index

router = APIRouter()


class SemanticMatchInput(BaseModel):
    """Input for semantic skill matching."""
    skill: str = Field(..., description="Skill name to match")
    top_k: int = Field(default=5, description="Number of results")
    threshold: float = Field(default=0.3, description="Minimum similarity score")


class SemanticMatchOutput(BaseModel):
    """Output for semantic skill matching."""
    query: str
    matches: List[Dict]
    method: str
    semantic_available: bool


@router.get(
    "/skills/semantic-match",
    summary="Semantic Skill Matching",
    description="""
    Find similar skills using semantic embeddings (sentence-transformers).
    
    Uses all-MiniLM-L6-v2 for meaning-based matching.
    Falls back to n-gram similarity if embeddings unavailable.
    """,
    tags=["Skills"]
)
async def semantic_match(
    skill: str = Query(..., description="Skill to match"),
    top_k: int = Query(5, description="Number of results"),
    threshold: float = Query(0.3, description="Minimum score")
):
    """
    Find similar skills using semantic embeddings.
    """
    from app.utils.similarity import is_semantic_matching_available
    from app.utils.embeddings import get_skills_index
    
    semantic_available = is_semantic_matching_available()
    method = "semantic" if semantic_available else "ngram"
    
    data_loader = get_data_loader()
    taxonomy = data_loader.load_skills_taxonomy()
    
    all_skills = []
    for category, skills in taxonomy.items():
        all_skills.extend(skills.keys())
    
    similarity = get_skill_similarity()
    similar = similarity.find_similar_skills(
        skill,
        all_skills,
        threshold=threshold,
        top_k=top_k,
        use_semantic=semantic_available
    )
    
    return {
        "query": skill,
        "matches": [
            {"skill": s, "score": round(sc, 4), "method": method}
            for s, sc in similar
        ],
        "method": method,
        "semantic_available": semantic_available,
        "count": len(similar)
    }


@router.post(
    "/skills/index/rebuild",
    summary="Rebuild Skills Embeddings Index",
    description="""
    Rebuild the ChromaDB embeddings index for semantic matching.
    
    Pre-computes embeddings for all skills in the taxonomy.
    """,
    tags=["Skills"]
)
async def rebuild_index(force: bool = False):
    """
    Rebuild the skills embeddings index.
    """
    result = rebuild_skills_index(force=force)
    
    if result.get("success"):
        return {
            "success": True,
            "skills_indexed": result.get("skills_indexed", 0),
            "variants_indexed": result.get("variants_indexed", 0),
            "rebuilt": result.get("rebuilt", False)
        }
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=result.get("error", "Failed to build index")
    )


@router.get(
    "/skills/index/status",
    summary="Get Index Status",
    description="Get the status of the embeddings index",
    tags=["Skills"]
)
async def get_index_status():
    """Get index status."""
    index = get_skills_index()
    stats = index.get_index_stats()
    
    return {
        "available": stats.get("vector_store_available", False),
        "model": stats.get("embedding_model"),
        "indexed_embeddings": stats.get("indexed_embeddings", 0),
        "taxonomy_skills": stats.get("taxonomy_skills", 0)
    }


@router.get(
    "/skills/ontology/{skill_id}",
    summary="Get Skill Hierarchy",
    description="""
    Get the hierarchical details of a skill.
    
    Includes parent, children, and related skills.
    """,
    tags=["Skills"]
)
async def get_skill_hierarchy_endpoint(skill_id: str):
    """
    Get skill hierarchy details.
    """
    hierarchy = get_skill_hierarchy(skill_id)
    
    if not hierarchy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found in ontology"
        )
    
    return hierarchy


@router.get(
    "/skills/related/{skill_id}",
    summary="Get Related Skills",
    description="Get skills related to a given skill",
    tags=["Skills"]
)
async def get_related_skills_endpoint(skill_id: str):
    """
    Get related skills.
    """
    related = get_related_skills(skill_id)
    
    if not related:
        return {
            "skill_id": skill_id,
            "related": [],
            "message": "No related skills found"
        }
    
    return {
        "skill_id": skill_id,
        "related": related
    }


@router.get(
    "/skills/ontology-tree",
    summary="Get Full Skill Ontology Tree",
    description="Get the complete skill hierarchy as a tree",
    tags=["Skills"]
)
async def get_ontology_tree():
    """Get full ontology tree."""
    ontology = get_skill_ontology()
    tree = ontology.get_skill_tree()
    
    return tree


@router.get(
    "/skills/levels",
    summary="Get Skills by Level",
    description="Get all skills at a specific level",
    tags=["Skills"]
)
async def get_skills_by_level(level: str = Query(..., description="Level: foundational, beginner, intermediate, advanced")):
    """Get skills by level."""
    ontology = get_skill_ontology()
    skills = ontology.get_skills_by_level(level)
    
    return {
        "level": level,
        "skills": [
            {"skill_id": s, "name": ontology.get_name(s)}
            for s in skills
        ],
        "count": len(skills)
    }


@router.post(
    "/similar-skills",
    summary="Find Similar Skills (Legacy)",
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
    top_k: int = 5,
    use_semantic: bool = True
):
    """
    Find skills similar to the target skill.
    
    Args:
        target_skill: Skill to find matches for
        threshold: Minimum similarity score (0-1)
        top_k: Maximum number of results
        use_semantic: Whether to use semantic matching first
        
    Returns:
        List of similar skills with scores
    """
    similarity = get_skill_similarity()
    data_loader = get_data_loader()
    
    taxonomy = data_loader.load_skills_taxonomy()
    all_skills = []
    
    for category, skills in taxonomy.items():
        all_skills.extend(skills.keys())
    
    roles = data_loader.load_role_profiles()
    for role_key, role_data in roles.items():
        for skill_data in role_data.get("required_skills", []):
            if skill_data["skill"] not in all_skills:
                all_skills.append(skill_data["skill"])
    
    similar = similarity.find_similar_skills(
        target_skill,
        all_skills,
        threshold=threshold,
        top_k=top_k,
        use_semantic=use_semantic
    )
    
    semantic_available = is_semantic_matching_available()
    method = "semantic" if semantic_available and use_semantic else "ngram"
    
    return {
        "target_skill": target_skill,
        "similar_skills": [
            {"skill": skill, "similarity": round(score, 3)}
            for skill, score in similar
        ],
        "method": method,
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
async def find_closest_match(
    query: str,
    options: List[str],
    use_semantic: bool = True
):
    """
    Find closest matching skill.
    
    Args:
        query: Query string
        options: List of possible matches
        use_semantic: Use semantic matching
        
    Returns:
        Best match with similarity score
    """
    similarity = get_skill_similarity()
    
    result = similarity.find_similar_skills(
        query,
        options,
        threshold=0.0,
        top_k=1,
        use_semantic=use_semantic
    )
    
    semantic_available = is_semantic_matching_available()
    method = "semantic" if semantic_available and use_semantic else "ngram"
    
    if result:
        return {
            "query": query,
            "best_match": result[0][0],
            "similarity": round(result[0][1], 3),
            "method": method,
            "found": True
        }
    
    return {
        "query": query,
        "best_match": None,
        "similarity": 0.0,
        "method": method,
        "found": False
    }