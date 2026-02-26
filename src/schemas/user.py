"""ユーザースキーマ"""
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """ユーザー作成"""
    cd: str
    name: str


class UserUpdate(BaseModel):
    """ユーザー更新"""
    cd: str
    name: str


class UserOut(BaseModel):
    """ユーザー出力"""
    id: int
    cd: str
    name: str
    is_active: int | None = 1

    model_config = ConfigDict(from_attributes=True)
