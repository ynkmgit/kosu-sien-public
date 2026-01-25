"""ユーザー属性選択肢CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はUserAttributeOptionServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import UserAttributeOptionService
from .common import templates, render_edit_actions, get_attribute_type_or_404

router = APIRouter(prefix="/user-attribute-types/{type_id}/options", tags=["user-attribute-options"])


def render_row(o, type_id: int, editing=False):
    """選択肢行HTML生成"""
    code = escape(o['code'])
    name = escape(o['name'])
    sort_order = o['sort_order']

    if editing:
        base_path = f"/user-attribute-types/{type_id}/options"
        return f"""
        <tr id="attr-option-{o['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="code" value="{code}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="number" name="sort_order" value="{sort_order}" class="edit-input" step="1" min="0"></td>
            <td>{render_edit_actions("attr-option", o['id'], base_path)}</td>
        </tr>"""

    return f"""
    <tr id="attr-option-{o['id']}">
        <td class="cd-cell">{code}</td>
        <td class="name-cell">{name}</td>
        <td>{sort_order}</td>
        <td><div class="actions-cell">
            <button hx-get="/user-attribute-types/{type_id}/options/{o['id']}/edit" hx-target="#attr-option-{o['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    type_id: int,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    attr_type = get_attribute_type_or_404(type_id)
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "user_attribute_options.html", {
        "active": "user-attributes",
        "attr_type": attr_type,
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(type_id: int):
    """選択肢一覧取得"""
    get_attribute_type_or_404(type_id)
    rows = UserAttributeOptionService.get_all(type_id)
    tbody = "".join(render_row(r, type_id) for r in rows)
    return HTMLResponse(f"<tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(type_id: int, id: int):
    get_attribute_type_or_404(type_id)
    o = UserAttributeOptionService.get_by_id(id, type_id)
    if not o:
        raise HTTPException(status_code=404, detail="Option not found")
    return HTMLResponse(render_row(o, type_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(type_id: int, id: int):
    get_attribute_type_or_404(type_id)
    o = UserAttributeOptionService.get_by_id(id, type_id)
    if not o:
        raise HTTPException(status_code=404, detail="Option not found")
    return HTMLResponse(render_row(o, type_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(type_id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    get_attribute_type_or_404(type_id)
    o = UserAttributeOptionService.create(type_id, code, name, sort_order)
    return HTMLResponse(render_row(o, type_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(type_id: int, id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    get_attribute_type_or_404(type_id)
    o = UserAttributeOptionService.update(id, type_id, code, name, sort_order)
    if not o:
        raise HTTPException(status_code=404, detail="Option not found")
    return HTMLResponse(render_row(o, type_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(type_id: int, id: int):
    get_attribute_type_or_404(type_id)
    if UserAttributeOptionService.is_in_use(id):
        raise HTTPException(status_code=400, detail="この選択肢は使用中のため削除できません")
    if not UserAttributeOptionService.delete(id, type_id):
        raise HTTPException(status_code=404, detail="Option not found")
    return HTMLResponse("")
