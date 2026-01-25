"""案件 JSON API"""
from fastapi import APIRouter, HTTPException, Query

from services import IssueService, ProjectService
from schemas import IssueCreate, IssueUpdate, IssueOut

router = APIRouter(prefix="/issues", tags=["api-issues"])


@router.get("", response_model=list[IssueOut])
def list_issues(
    project_id: int = Query(default=None, description="プロジェクトID"),
    sort: str = Query(default="cd", description="ソート列"),
    order: str = Query(default="asc", description="昇順/降順"),
    q: str = Query(default="", description="検索キーワード")
):
    """案件一覧"""
    return IssueService.get_all(project_id=project_id, sort=sort, order=order, q=q)


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int):
    """案件詳細"""
    issue = IssueService.get_by_id(issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.post("", response_model=IssueOut, status_code=201)
def create_issue(body: IssueCreate):
    """案件作成"""
    # プロジェクト存在確認
    if not ProjectService.get_by_id(body.project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    return IssueService.create(
        project_id=body.project_id,
        cd=body.cd,
        name=body.name,
        status=body.status,
        description=body.description
    )


@router.put("/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, body: IssueUpdate):
    """案件更新"""
    issue = IssueService.update(
        issue_id=issue_id,
        cd=body.cd,
        name=body.name,
        status=body.status,
        description=body.description
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.delete("/{issue_id}", status_code=204)
def delete_issue(issue_id: int):
    """案件削除"""
    if not IssueService.delete(issue_id):
        raise HTTPException(status_code=404, detail="Issue not found")
