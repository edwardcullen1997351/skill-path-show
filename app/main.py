"""
Skill Path Show - FastAPI Backend Application
==============================================

A backend service that extracts skills from college curricula,
identifies skill gaps for target job roles, and generates
MECE (Mutually Exclusive, Collectively Exhaustive) subject recommendations.

Author: Skill Path Show Team
Version: 1.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    curriculum,
    roles,
    gap_analysis,
    recommendations,
    simulation,
    similarity,
    llm,
    user,
    progress,
    adaptive,
)

# Create FastAPI application instance
app = FastAPI(
    title="Skill Path Show API",
    description="""
    ## Overview
    This API provides backend services for extracting skills from college curricula,
    identifying skill gaps for target job roles, and generating MECE subject recommendations.

    ## Features
    - **Curriculum Processing**: Extract skills from curriculum text/JSON
    - **Role Profiles**: Get required skills for various job roles
    - **Gap Analysis**: Identify skill gaps between current skills and target role
    - **MECE Recommendations**: Generate minimal, non-overlapping subject recommendations
    - **Coverage Simulation**: Simulate skill coverage for selected subjects
    
    ## Core Modules
    1. Curriculum Processing Module - POST /parse-curriculum
    2. Role Skill Profile Module - GET /roles/{role_name}
    3. Skill Gap Analysis Engine - POST /analyze-gap
    4. MECE Recommendation Engine - POST /recommend-subjects
    5. Coverage Simulation - POST /simulate-selection
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Skill Path Show Team",
        "email": "team@skillpathshow.com"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(curriculum.router, prefix="/api/v1", tags=["Curriculum"])
app.include_router(roles.router, prefix="/api/v1", tags=["Roles"])
app.include_router(gap_analysis.router, prefix="/api/v1", tags=["Gap Analysis"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(simulation.router, prefix="/api/v1", tags=["Simulation"])
app.include_router(similarity.router, prefix="/api/v1", tags=["Similarity"])
app.include_router(llm.router, prefix="/api/v1", tags=["LLM"])
app.include_router(user.router, prefix="/api/v1", tags=["Users"])
app.include_router(progress.router, prefix="/api/v1", tags=["Progress"])
app.include_router(adaptive.router, prefix="/api/v1", tags=["Adaptive"])


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - returns basic API information.
    
    Returns:
        dict: Basic API information and available endpoints
    """
    return {
        "name": "Skill Path Show API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "curriculum": "/api/v1/parse-curriculum",
            "roles": "/api/v1/roles/{role_name}",
            "gap_analysis": "/api/v1/analyze-gap",
            "recommendations": "/api/v1/recommend-subjects",
            "simulation": "/api/v1/simulate-selection"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint - returns API health status.
    
    Returns:
        dict: Health status of the API
    """
    return {
        "status": "healthy",
        "service": "skill-path-show-api"
    }


# Run info for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )