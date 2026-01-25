"""プロジェクト JSON API"""
from fastapi import APIRouter, HTTPException, Query

from services import ProjectService
from schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectSummary

router = APIRouter(prefix="/projects", tags=["api-projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    sort: str = Query(default="cd", description="ソート列"),
    order: str = Query(default="asc", description="昇順/降順"),
    q: str = Query(default="", description="検索キーワード")
):
    """プロジェクト一覧"""
    return ProjectService.get_all(sort=sort, order=order, q=q)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int):
    """プロジェクト詳細"""
    project = ProjectService.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary(project_id: int):
    """プロジェクトサマリー"""
    project = ProjectService.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectService.get_summary(project_id)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate):
    """プロジェクト作成"""
    return ProjectService.create(cd=body.cd, name=body.name, description=body.description)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectUpdate):
    """プロジェクト更新"""
    project = ProjectService.update(
        project_id=project_id,
        cd=body.cd,
        name=body.name,
        description=body.description
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int):
    """プロジェクト削除"""
    if not ProjectService.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
