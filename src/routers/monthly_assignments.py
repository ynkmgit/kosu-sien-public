"""月次アサインCRUD

責務: HTTPルーティングのみ
データ操作はMonthlyAssignmentServiceに委譲
HTML生成はmonthly_assignment_rendererに委譲
"""
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import MonthlyAssignmentService, UserService, ProjectService
from .common import (
    templates, get_current_month, parse_month,
    FilterParams, get_filter_params
)
from .common.monthly_assignment_renderer import render_grid

router = APIRouter(prefix="/monthly-assignments", tags=["monthly_assignments"])


@router.get("", response_class=HTMLResponse)
def page(request: Request, month: str = None, mode: str = "simple", filters: FilterParams = Depends(get_filter_params)):
    """月次アサインページ"""
    if month:
        year_month = parse_month(month)
    else:
        year_month = get_current_month()

    # modeの検証
    if mode not in ("simple", "detail"):
        mode = "simple"

    return templates.TemplateResponse(request, "monthly_assignments.html", {
        "active": "monthly_assignments",
        "year_month": year_month,
        "mode": mode,
        "filter_params": filters.to_dict(),
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(month: str = None, mode: str = "simple"):
    """グリッド取得"""
    if month:
        year_month = parse_month(month)
    else:
        year_month = get_current_month()

    # modeの検証
    if mode not in ("simple", "detail"):
        mode = "simple"

    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    assignments = MonthlyAssignmentService.get_assignments_for_month(year_month)
    actuals = MonthlyAssignmentService.get_actuals_for_month(year_month) if mode == "detail" else {}

    return HTMLResponse(render_grid(year_month, users, projects, assignments, actuals, mode))


@router.post("", response_class=HTMLResponse)
def upsert_assignment(
    user_id: int = Form(...),
    project_id: int = Form(...),
    year_month: str = Form(...),
    planned_hours: float = Form(...)
):
    """アサイン追加/更新"""
    year_month = parse_month(year_month)

    # ユーザーの存在確認と有効確認
    user = MonthlyAssignmentService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # プロジェクトの存在確認
    project = MonthlyAssignmentService.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 新規作成時の無効ユーザーチェック
    existing = MonthlyAssignmentService.get_assignment(user_id, project_id, year_month)
    if not existing and planned_hours > 0 and user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーにはアサインできません")

    try:
        MonthlyAssignmentService.upsert(user_id, project_id, year_month, planned_hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return HTMLResponse("")


@router.delete("/{id}", response_class=HTMLResponse)
def delete_assignment(id: int):
    """アサイン削除"""
    existing = MonthlyAssignmentService.get_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Assignment not found")

    MonthlyAssignmentService.delete(id)
    return HTMLResponse("")
