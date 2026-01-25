"""実績スキーマ"""
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class WorkLogCreate(BaseModel):
    """実績作成/更新"""
    task_id: int
    user_id: int
    work_date: date
    hours: float = Field(ge=0)


class WorkLogOut(BaseModel):
    """実績出力"""
    id: int
    task_id: int
    user_id: int
    work_date: str
    hours: float
    task_cd: str | None = None
    task_name: str | None = None
    issue_id: int | None = None
    issue_cd: str | None = None
    issue_name: str | None = None
    project_id: int | None = None
    project_cd: str | None = None
    project_name: str | None = None
    user_cd: str | None = None
    user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
