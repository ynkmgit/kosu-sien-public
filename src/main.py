"""工数支援システム - FastAPI + HTMX"""
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import init_db
from middleware import EncodingValidationMiddleware
from routers.common import templates
from services import DashboardService
from routers import (
    projects_router,
    users_router,
    issues_router,
    statuses_router,
    tasks_router,
    issue_estimates_router,
    task_assignees_router,
    monthly_assignments_router,
    work_logs_router,
    work_report_router,
    search_router,
    task_progress_router,
    user_attribute_types_router,
    user_attribute_options_router,
    user_settings_router,
    api_v1_router,
)

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(EncodingValidationMiddleware)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(projects_router)
app.include_router(users_router)
app.include_router(issues_router)
app.include_router(statuses_router)
app.include_router(tasks_router)
app.include_router(issue_estimates_router)
app.include_router(task_assignees_router)
app.include_router(monthly_assignments_router)
app.include_router(work_logs_router)
app.include_router(work_report_router)
app.include_router(search_router)
app.include_router(task_progress_router)
app.include_router(user_attribute_types_router)
app.include_router(user_attribute_options_router)
app.include_router(user_settings_router)
app.include_router(api_v1_router)


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    today = date.today()
    year_month = today.strftime("%Y-%m")
    filter_params = {"user": user, "project": project, "issue": issue}

    today_hours = DashboardService.get_today_hours(today)
    monthly = DashboardService.get_monthly_stats(year_month)
    counts = DashboardService.get_counts()

    return templates.TemplateResponse(request, "index.html", {
        "active": "home",
        "filter_params": filter_params,
        "today_hours": today_hours,
        "monthly_planned": monthly['planned'],
        "monthly_actual": monthly['actual'],
        "project_count": counts['project_count'],
        "user_count": counts['user_count'],
    })
