"""
Skill Path Show API Application.

A FastAPI backend service for:
- Extracting skills from college curricula
- Identifying skill gaps for target job roles
- Generating MECE subject/elective recommendations
"""

__version__ = "1.0.0"
__author__ = "Skill Path Show Team"

from app.main import app

__all__ = ["app"]