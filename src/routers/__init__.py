from .projects import router as projects_router
from .users import router as users_router
from .issues import router as issues_router
from .statuses import router as statuses_router
from .tasks import router as tasks_router
from .tasks import task_progress_router
from .issue_estimates import router as issue_estimates_router
from .task_assignees import router as task_assignees_router
from .monthly_assignments import router as monthly_assignments_router
from .work_logs import router as work_logs_router
from .work_report import router as work_report_router
from .search import router as search_router
from .user_attribute_types import router as user_attribute_types_router
from .user_attribute_options import router as user_attribute_options_router
from .user_settings import router as user_settings_router
from .api import api_v1_router

__all__ = [
    "projects_router",
    "users_router",
    "issues_router",
    "statuses_router",
    "tasks_router",
    "issue_estimates_router",
    "task_assignees_router",
    "monthly_assignments_router",
    "work_logs_router",
    "work_report_router",
    "search_router",
    "task_progress_router",
    "user_attribute_types_router",
    "user_attribute_options_router",
    "user_settings_router",
    "api_v1_router",
]
