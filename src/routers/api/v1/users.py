"""ユーザー JSON API"""
from fastapi import APIRouter, HTTPException, Query

from services import UserService
from schemas import UserCreate, UserUpdate, UserOut

router = APIRouter(prefix="/users", tags=["api-users"])


@router.get("", response_model=list[UserOut])
def list_users(
    sort: str = Query(default="cd", description="ソート列"),
    order: str = Query(default="asc", description="昇順/降順"),
    q: str = Query(default="", description="検索キーワード"),
    active_only: bool = Query(default=False, description="有効ユーザーのみ")
):
    """ユーザー一覧"""
    return UserService.get_all(sort=sort, order=order, q=q, active_only=active_only)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    """ユーザー詳細"""
    user = UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserOut, status_code=201)
def create_user(body: UserCreate):
    """ユーザー作成"""
    return UserService.create(cd=body.cd, name=body.name, email=body.email)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate):
    """ユーザー更新"""
    user = UserService.update(
        user_id=user_id,
        cd=body.cd,
        name=body.name,
        email=body.email
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int):
    """ユーザー削除"""
    if not UserService.delete(user_id):
        raise HTTPException(status_code=404, detail="User not found")
