"""実績 JSON API"""
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from services import WorkLogService
from schemas import WorkLogCreate, WorkLogOut

router = APIRouter(prefix="/work-logs", tags=["api-work-logs"])


@router.get("", response_model=list[WorkLogOut])
def list_work_logs(
    user_id: int = Query(default=None, description="ユーザーID"),
    task_id: int = Query(default=None, description="作業ID"),
    project_id: int = Query(default=None, description="プロジェクトID"),
    issue_id: int = Query(default=None, description="案件ID"),
    start_date: date = Query(default=None, description="開始日"),
    end_date: date = Query(default=None, description="終了日")
):
    """実績一覧"""
    return WorkLogService.get_all(
        user_id=user_id,
        task_id=task_id,
        project_id=project_id,
        issue_id=issue_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/{work_log_id}", response_model=WorkLogOut)
def get_work_log(work_log_id: int):
    """実績詳細"""
    work_log = WorkLogService.get_by_id(work_log_id)
    if not work_log:
        raise HTTPException(status_code=404, detail="Work log not found")
    return work_log


@router.post("", response_model=WorkLogOut | None, status_code=201)
def create_or_update_work_log(body: WorkLogCreate):
    """実績作成/更新（upsert）

    hours=0の場合は削除され、nullが返る
    """
    try:
        return WorkLogService.upsert(
            task_id=body.task_id,
            user_id=body.user_id,
            work_date=body.work_date,
            hours=body.hours
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{work_log_id}", status_code=204)
def delete_work_log(work_log_id: int):
    """実績削除"""
    if not WorkLogService.delete(work_log_id):
        raise HTTPException(status_code=404, detail="Work log not found")
