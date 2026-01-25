"""作業 JSON API"""
from fastapi import APIRouter, HTTPException, Query

from services import TaskService, IssueService
from schemas import TaskCreate, TaskUpdate, TaskOut, TaskProgressUpdate

router = APIRouter(prefix="/tasks", tags=["api-tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    issue_id: int = Query(default=None, description="案件ID"),
    project_id: int = Query(default=None, description="プロジェクトID"),
    sort: str = Query(default="cd", description="ソート列"),
    order: str = Query(default="asc", description="昇順/降順"),
    q: str = Query(default="", description="検索キーワード")
):
    """作業一覧"""
    return TaskService.get_all(
        issue_id=issue_id,
        project_id=project_id,
        sort=sort,
        order=order,
        q=q
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    """作業詳細"""
    task = TaskService.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskOut, status_code=201)
def create_task(body: TaskCreate):
    """作業作成"""
    # 案件存在確認
    if not IssueService.get_by_id(body.issue_id):
        raise HTTPException(status_code=404, detail="Issue not found")

    return TaskService.create(
        issue_id=body.issue_id,
        cd=body.cd,
        name=body.name,
        description=body.description
    )


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate):
    """作業更新"""
    task = TaskService.update(
        task_id=task_id,
        cd=body.cd,
        name=body.name,
        description=body.description
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}/progress", status_code=204)
def update_task_progress(task_id: int, body: TaskProgressUpdate):
    """進捗率更新"""
    try:
        if not TaskService.update_progress(task_id, body.progress_rate):
            raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int):
    """作業削除"""
    if not TaskService.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
