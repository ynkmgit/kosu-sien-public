"""案件スキーマ"""
from pydantic import BaseModel, ConfigDict


class IssueCreate(BaseModel):
    """案件作成"""
    project_id: int
    cd: str
    name: str
    status: str = "open"


class IssueUpdate(BaseModel):
    """案件更新"""
    cd: str
    name: str
    status: str


class IssueOut(BaseModel):
    """案件出力"""
    id: int
    cd: str
    name: str
    status: str | None
    project_id: int
    project_cd: str | None = None
    project_name: str | None = None
    status_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
