"""
Coverage simulation router.

This router handles the POST /simulate-selection endpoint
for simulating skill coverage with selected subjects.
"""

from fastapi import APIRouter, HTTPException, status
from app.models.simulation import SimulationInput, SimulationOutput
from app.services import get_simulation_service

router = APIRouter()


@router.post(
    "/simulate-selection",
    response_model=SimulationOutput,
    summary="Simulate Coverage",
    description="""
    Simulate skill coverage for selected subjects against a target role.
    
    This endpoint shows what the coverage would look like if a student
    takes certain subjects, helping them make informed decisions.
    
    ## Output Details
    - **updated_coverage_percent**: Coverage percentage after adding subjects
    - **remaining_gaps**: Skills still not covered
    - **skill_coverage_breakdown**: Detailed coverage per skill
      - skill: Skill name
      - covered: Whether the skill is covered
      - weightage: Importance of the skill for the role
      - source_subjects: Subjects that provide this skill
    """,
    tags=["Simulation"]
)
async def simulate_selection(input_data: SimulationInput) -> SimulationOutput:
    """
    Simulate skill coverage for selected subjects.
    
    Args:
        input_data: SimulationInput with selected_subjects and target_role
        
    Returns:
        SimulationOutput with coverage details
        
    Raises:
        HTTPException: If no subjects selected or role not found
    """
    if not input_data.selected_subjects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected subjects list cannot be empty"
        )
    
    service = get_simulation_service()
    
    try:
        result = service.simulate_coverage(input_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error simulating coverage: {str(e)}"
        )


@router.post(
    "/simulate-selection/optimal",
    summary="Calculate Optimal Additions",
    description="""
    Calculate which subjects would optimally increase coverage.
    
    Given current subjects, recommends additional subjects that
    would fill the most gaps.
    """,
    tags=["Simulation"]
)
async def get_optimal_additions(
    current_subjects: list,
    target_role: str,
    max_additions: int = 3
):
    """
    Get optimal subject additions.
    
    Args:
        current_subjects: Currently selected subjects
        target_role: Target role key
        max_additions: Maximum subjects to recommend
        
    Returns:
        List of recommended subjects to add
    """
    service = get_simulation_service()
    
    try:
        result = service.calculate_optimal_additions(
            current_subjects=current_subjects,
            target_role=target_role,
            max_additions=max_additions
        )
        return {
            "recommendations": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating optimal additions: {str(e)}"
        )


@router.get(
    "/simulation/health",
    summary="Simulation Service Health",
    tags=["Simulation"]
)
async def simulation_health():
    """Health check for simulation service."""
    return {
        "status": "healthy",
        "service": "simulation",
        "version": "1.0.0"
    }