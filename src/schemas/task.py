"""作業スキーマ"""
from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """作業作成"""
    issue_id: int
    cd: str
    name: str
    description: str = ""


class TaskUpdate(BaseModel):
    """作業更新"""
    cd: str
    name: str
    description: str = ""


class TaskProgressUpdate(BaseModel):
    """進捗率更新"""
    progress_rate: int = Field(ge=0, le=100)


class TaskOut(BaseModel):
    """作業出力"""
    id: int
    cd: str
    name: str
    description: str | None
    issue_id: int
    progress_rate: int | None = 0
    sort_order: int | None = 0
    issue_cd: str | None = None
    issue_name: str | None = None
    project_id: int | None = None
    project_cd: str | None = None
    project_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
