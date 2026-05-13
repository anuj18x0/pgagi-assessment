from fastapi import APIRouter
from app.api.v1 import health, resume, interview, session

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, prefix="/health", tags=["System"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
api_router.include_router(interview.router, prefix="/interview", tags=["Interview"])
api_router.include_router(session.router, prefix="/session", tags=["Session"])
