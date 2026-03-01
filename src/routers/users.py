"""ユーザーCRUD

責務: HTTPルーティングのみ
データ操作はUserServiceに委譲
HTML生成はuser_rendererに委譲
"""
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import UserService
from .common import templates, get_user_or_404, FilterParams, get_filter_params
from .common.user_renderer import render_row, render_thead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_class=HTMLResponse)
def page(request: Request, filters: FilterParams = Depends(get_filter_params)):
    return templates.TemplateResponse(request, "users.html", {
        "active": "users", "filter_params": filters.to_dict()
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(sort: str = "cd", order: str = "asc", q: str = ""):
    """ユーザー一覧取得（検索・ソート対応）"""
    attr_types = UserService.get_attribute_types()
    rows = UserService.get_all(sort=sort, order=order, q=q)

    # N+1回避: 全ユーザーの属性を一括取得
    all_attrs = UserService.get_all_attributes([r['id'] for r in rows])
    tbody = ""
    for r in rows:
        tbody += render_row(r, attr_types=attr_types, user_attrs=all_attrs.get(r['id'], {}))

    thead = render_thead(sort, order, attr_types)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(id: int):
    u = UserService.get_by_id(id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    attr_types = UserService.get_attribute_types()
    user_attrs = UserService.get_attributes(id)
    return HTMLResponse(render_row(u, attr_types=attr_types, user_attrs=user_attrs))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(id: int):
    u = UserService.get_by_id(id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    attr_types = UserService.get_attribute_types()
    user_attrs = UserService.get_attributes(id)
    return HTMLResponse(render_row(u, editing=True, attr_types=attr_types, user_attrs=user_attrs))


@router.post("", response_class=HTMLResponse)
def create(cd: str = Form(...), name: str = Form(...)):
    attr_types = UserService.get_attribute_types()
    u = UserService.create(cd=cd, name=name)
    return HTMLResponse(render_row(u, attr_types=attr_types, user_attrs={}))


@router.put("/{id}", response_class=HTMLResponse)
async def update(id: int, request: Request, cd: str = Form(...), name: str = Form(...)):
    attr_types = UserService.get_attribute_types()

    # ユーザー更新
    u = UserService.update(user_id=id, cd=cd, name=name)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # フォームデータを取得して属性を更新
    form_data = await request.form()
    for t in attr_types:
        attr_key = f"attr_{t['id']}"
        if attr_key in form_data:
            option_id = form_data[attr_key]
            UserService.set_attribute(id, t['id'], int(option_id) if option_id else None)

    user_attrs = UserService.get_attributes(id)
    return HTMLResponse(render_row(u, attr_types=attr_types, user_attrs=user_attrs))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(id: int):
    if not UserService.delete(id):
        raise HTTPException(status_code=404, detail="User not found")
    return HTMLResponse("")
