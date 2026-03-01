"""担当割当CRUD

責務: HTTPルーティングのみ
データ操作はTaskAssigneeServiceに委譲
HTML生成はtask_assignee_rendererに委譲
"""
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import TaskAssigneeService, UserService
from .common import templates, get_project_or_404, FilterParams, get_filter_params
from .common.task_assignee_renderer import render_matrix

router = APIRouter(prefix="/projects/{project_id}/assignees", tags=["task_assignees"])


@router.get("", response_class=HTMLResponse)
def page(request: Request, project_id: int, filters: FilterParams = Depends(get_filter_params)):
    proj = get_project_or_404(project_id)
    return templates.TemplateResponse(request, "task_assignees.html", {
        "active": "projects",
        "project": proj,
        "filter_params": filters.to_dict(),
    })


@router.get("/matrix", response_class=HTMLResponse)
def get_matrix(project_id: int):
    """マトリクス取得"""
    get_project_or_404(project_id)
    users = UserService.get_active_list()
    tasks = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assignments = TaskAssigneeService.get_all_assignments(project_id)
    return HTMLResponse(render_matrix(project_id, users, tasks, assignments))


@router.post("/toggle", response_class=HTMLResponse)
def toggle_assignment(project_id: int, task_id: int = Form(...), user_id: int = Form(...)):
    """担当割当のトグル"""
    get_project_or_404(project_id)

    # 作業の存在確認とプロジェクト所属確認
    task = TaskAssigneeService.get_task_in_project(task_id, project_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ユーザーの存在確認と有効確認
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 既存の割当を確認
    existing = TaskAssigneeService.get_assignment(task_id, user_id)

    if existing:
        # 割当解除
        TaskAssigneeService.delete(existing['id'])
    else:
        # 新規割当（無効ユーザーはブロック）
        if user['is_active'] == 0:
            raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")
        TaskAssigneeService.create(task_id, user_id)

    # マトリクス再取得
    users = UserService.get_active_list()
    tasks = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assignments = TaskAssigneeService.get_all_assignments(project_id)

    return HTMLResponse(render_matrix(project_id, users, tasks, assignments))


@router.post("", response_class=HTMLResponse)
def create_assignment(project_id: int, task_id: int = Form(...), user_id: int = Form(...)):
    """担当割当追加"""
    get_project_or_404(project_id)

    # 作業の存在確認
    task = TaskAssigneeService.get_task_in_project(task_id, project_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ユーザーの存在確認と有効確認
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")

    # 既存チェック（既にあれば何もしない）
    existing = TaskAssigneeService.get_assignment(task_id, user_id)
    if not existing:
        TaskAssigneeService.create(task_id, user_id)

    return HTMLResponse("")


@router.delete("/{id}", response_class=HTMLResponse)
def delete_assignment(project_id: int, id: int):
    """担当割当解除"""
    get_project_or_404(project_id)

    # 割当の存在確認とプロジェクト所属確認
    assignment = TaskAssigneeService.get_assignment_in_project(id, project_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    TaskAssigneeService.delete(id)
    return HTMLResponse("")
