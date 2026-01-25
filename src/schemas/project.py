"""プロジェクトスキーマ"""
from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    """プロジェクト作成"""
    cd: str
    name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    """プロジェクト更新"""
    cd: str
    name: str
    description: str = ""


class ProjectOut(BaseModel):
    """プロジェクト出力"""
    id: int
    cd: str
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    """プロジェクトサマリー"""
    issue_count: int
    task_count: int
    estimate_total: float
    actual_total: float
    consumption_rate: float
