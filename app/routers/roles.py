"""
Role profile router.

This router handles the GET /roles/{role_name} endpoint
for retrieving role profiles and required skills.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from app.models.roles import RoleProfile, RoleListResponse
from app.services import get_role_service
from app.utils.cache import get_cache_stats

router = APIRouter()


@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="List All Roles",
    description="""
    Get a list of all available job roles in the system.
    
    Returns role keys that can be used in other endpoints
    like `/analyze-gap` and `/simulate-selection`.
    """,
    tags=["Roles"]
)
async def list_roles() -> RoleListResponse:
    """
    Get list of all available roles.
    
    Returns:
        RoleListResponse with all role keys
    """
    service = get_role_service()
    return service.get_all_roles()


@router.get(
    "/roles/{role_name}",
    response_model=RoleProfile,
    summary="Get Role Profile",
    description="""
    Get detailed information about a specific job role.
    
    Returns the role name, description, and required skills
    with their weightages (importance levels).
    
    ## Role Keys
    Available role keys:
    - frontend_developer
    - backend_developer
    - data_analyst
    - full_stack_developer
    - devops_engineer
    - data_scientist
    - ml_engineer
    - software_engineer
    """,
    tags=["Roles"]
)
async def get_role(role_name: str) -> RoleProfile:
    """
    Get a specific role profile by role key.
    
    Args:
        role_name: Role key (e.g., 'frontend_developer')
        
    Returns:
        RoleProfile with required skills and weightages
        
    Raises:
        HTTPException: If role not found
    """
    service = get_role_service()
    role = service.get_role(role_name)
    
    if not role:
        available_roles = service.get_all_roles().roles
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found",
            headers={"X-Available-Roles": ", ".join(available_roles)}
        )
    
    return role


@router.get(
    "/roles/search/",
    response_model=List[RoleProfile],
    summary="Search Roles",
    description="""
    Search for roles by query string.
    
    Matches against role name and description.
    """,
    tags=["Roles"]
)
async def search_roles(q: str = Query(..., min_length=1)) -> List[RoleProfile]:
    """
    Search roles by query string.
    
    Args:
        q: Search query
        
    Returns:
        List of matching role profiles
    """
    service = get_role_service()
    results = service.search_roles(q)
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No roles found matching '{q}'"
        )
    
    return results


@router.get(
    "/roles/{role_name}/skills",
    response_model=List[str],
    summary="Get Role Skills",
    description="""
    Get list of required skill keys for a specific role.
    
    Returns just the skill names without weightages.
    """,
    tags=["Roles"]
)
async def get_role_skills(role_name: str) -> List[str]:
    """
    Get required skills for a role.
    
    Args:
        role_name: Role key
        
    Returns:
        List of skill keys
        
    Raises:
        HTTPException: If role not found
    """
    service = get_role_service()
    skills = service.get_role_skills(role_name)
    
    if skills is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )
    
    return skills


@router.get(
    "/cache-stats",
    summary="Get Cache Statistics",
    description="Get statistics about the caching system",
    tags=["System"]
)
async def get_cache_statistics():
    """
    Get cache hit/miss statistics.
    
    Returns:
        Dict with cache stats for different caches
    """
    return get_cache_stats()