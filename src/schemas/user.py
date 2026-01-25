"""ユーザースキーマ"""
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """ユーザー作成"""
    cd: str
    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    """ユーザー更新"""
    cd: str
    name: str
    email: EmailStr


class UserOut(BaseModel):
    """ユーザー出力"""
    id: int
    cd: str
    name: str
    email: str
    is_active: int | None = 1

    model_config = ConfigDict(from_attributes=True)
