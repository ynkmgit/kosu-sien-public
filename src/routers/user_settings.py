"""ユーザー設定API

責務: HTTPルーティングのみ
データ操作はUserSettingServiceに委譲
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import UserSettingService

router = APIRouter(prefix="/api/user-settings", tags=["user-settings"])


class SettingValue(BaseModel):
    value: str | None = None


@router.get("/{user_id}/{key}")
def get_setting(user_id: int, key: str):
    """ユーザー設定を取得"""
    value = UserSettingService.get(user_id, key)
    return JSONResponse({"value": value})


@router.post("/{user_id}/{key}")
def save_setting(user_id: int, key: str, body: SettingValue):
    """ユーザー設定を保存（upsert）"""
    if not UserSettingService.save(user_id, key, body.value):
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse({"status": "ok"})


@router.delete("/{user_id}/{key}")
def delete_setting(user_id: int, key: str):
    """ユーザー設定を削除"""
    UserSettingService.delete(user_id, key)
    return JSONResponse({"status": "ok"})
