"""API v1 ルーター"""
from fastapi import APIRouter

from .projects import router as projects_router
from .users import router as users_router
from .issues import router as issues_router
from .tasks import router as tasks_router
from .work_logs import router as work_logs_router

router = APIRouter(prefix="/api/v1")

router.include_router(projects_router)
router.include_router(users_router)
router.include_router(issues_router)
router.include_router(tasks_router)
router.include_router(work_logs_router)
