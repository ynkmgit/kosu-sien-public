"""ユーザー属性タイプCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はUserAttributeTypeServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import UserAttributeTypeService
from .common import templates, render_edit_actions

router = APIRouter(prefix="/user-attribute-types", tags=["user-attribute-types"])


def render_row(t, option_count: int = 0, editing=False):
    """属性タイプ行HTML生成"""
    code = escape(t['code'])
    name = escape(t['name'])
    sort_order = t['sort_order']

    if editing:
        return f"""
        <tr id="attr-type-{t['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="code" value="{code}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="number" name="sort_order" value="{sort_order}" class="edit-input" step="1" min="0"></td>
            <td>{option_count}件</td>
            <td>{render_edit_actions("attr-type", t['id'], "/user-attribute-types")}</td>
        </tr>"""

    return f"""
    <tr id="attr-type-{t['id']}">
        <td class="cd-cell">{code}</td>
        <td class="name-cell">{name}</td>
        <td>{sort_order}</td>
        <td>{option_count}件</td>
        <td><div class="actions-cell">
            <button hx-get="/user-attribute-types/{t['id']}/edit" hx-target="#attr-type-{t['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
            <a href="/user-attribute-types/{t['id']}/options" class="btn btn-sm btn-primary">選択肢</a>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "user_attribute_types.html", {
        "active": "user-attributes",
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all():
    """属性タイプ一覧取得"""
    rows = UserAttributeTypeService.get_all()
    counts = UserAttributeTypeService.get_option_counts()
    tbody = "".join(render_row(r, counts.get(r['id'], 0)) for r in rows)
    return HTMLResponse(f"<tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(id: int):
    t = UserAttributeTypeService.get_by_id(id)
    if not t:
        raise HTTPException(status_code=404, detail="Attribute type not found")
    option_count = UserAttributeTypeService.get_option_count(id)
    return HTMLResponse(render_row(t, option_count))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(id: int):
    t = UserAttributeTypeService.get_by_id(id)
    if not t:
        raise HTTPException(status_code=404, detail="Attribute type not found")
    option_count = UserAttributeTypeService.get_option_count(id)
    return HTMLResponse(render_row(t, option_count, editing=True))


@router.post("", response_class=HTMLResponse)
def create(code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    t = UserAttributeTypeService.create(code, name, sort_order)
    return HTMLResponse(render_row(t, option_count=0))  # 新規作成時は選択肢0件


@router.put("/{id}", response_class=HTMLResponse)
def update(id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    t = UserAttributeTypeService.update(id, code, name, sort_order)
    if not t:
        raise HTTPException(status_code=404, detail="Attribute type not found")
    option_count = UserAttributeTypeService.get_option_count(id)
    return HTMLResponse(render_row(t, option_count))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(id: int):
    if UserAttributeTypeService.is_in_use(id):
        raise HTTPException(status_code=400, detail="この属性タイプは使用中のため削除できません")
    if not UserAttributeTypeService.delete(id):
        raise HTTPException(status_code=404, detail="Attribute type not found")
    return HTMLResponse("")
