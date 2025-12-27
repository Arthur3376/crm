"""Route modules"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api")

# Import and include all route modules
from .auth import router as auth_router
from .users import router as users_router
from .teachers import router as teachers_router
from .careers import router as careers_router
from .students import router as students_router
from .leads import router as leads_router
from .appointments import router as appointments_router
from .webhooks import router as webhooks_router
from .dashboard import router as dashboard_router
from .calendar import router as calendar_router

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(teachers_router)
api_router.include_router(careers_router)
api_router.include_router(students_router)
api_router.include_router(leads_router)
api_router.include_router(appointments_router)
api_router.include_router(webhooks_router)
api_router.include_router(dashboard_router)
api_router.include_router(calendar_router)
