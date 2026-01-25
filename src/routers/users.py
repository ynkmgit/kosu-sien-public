"""ユーザーCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はUserServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import UserService
from .common import templates, render_edit_actions, render_sortable_th, get_user_or_404

router = APIRouter(prefix="/users", tags=["users"])


def render_thead(sort: str, order: str, attr_types: list):
    """ソート状態を反映したテーブルヘッダー生成"""
    def col(name, label, css_class=None):
        return render_sortable_th(name, label, sort, order, "/users/list", "user-table", css_class)

    # 属性列のヘッダー
    attr_headers = "".join(f'<th class="col-code">{escape(t["name"])}</th>' for t in attr_types)

    return f"""<tr>
        {col("cd", "CD", "col-cd")}
        {col("name", "名前", "col-name")}
        {col("email", "メール")}
        {attr_headers}
        <th class="col-actions">操作</th>
    </tr>"""


def render_row(u, editing=False, attr_types=None, user_attrs=None):
    """ユーザー行HTML生成"""
    cd = escape(u['cd'] or '')
    name = escape(u['name'])
    email = escape(u['email'])

    if attr_types is None:
        attr_types = []
    if user_attrs is None:
        user_attrs = {}

    # 属性セルを生成
    attr_cells = []
    for t in attr_types:
        current = user_attrs.get(t['id'])
        if editing:
            # 編集モード: ドロップダウン
            options_html = '<option value="">--</option>'
            for opt in t['options']:
                selected = 'selected' if current and current['option_id'] == opt['id'] else ''
                options_html += f'<option value="{opt["id"]}" {selected}>{escape(opt["name"])}</option>'
            attr_cells.append(f'<td><select name="attr_{t["id"]}" class="edit-input">{options_html}</select></td>')
        else:
            # 通常モード: バッジ
            if current:
                attr_cells.append(f'<td><span class="badge">{escape(current["option_name"])}</span></td>')
            else:
                attr_cells.append('<td><span class="badge badge-empty">-</span></td>')

    attr_cells_html = "".join(attr_cells)

    if editing:
        return f"""
        <tr id="user-{u['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="cd" value="{cd}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="email" name="email" value="{email}" class="edit-input"></td>
            {attr_cells_html}
            <td>{render_edit_actions("user", u['id'], "/users")}</td>
        </tr>"""
    return f"""
    <tr id="user-{u['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell">{name}</td>
        <td class="email-cell">{email}</td>
        {attr_cells_html}
        <td><div class="actions-cell">
            <button hx-get="/users/{u['id']}/edit" hx-target="#user-{u['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
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
    return templates.TemplateResponse(request, "users.html", {
        "active": "users", "filter_params": filter_params
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(sort: str = "cd", order: str = "asc", q: str = ""):
    """ユーザー一覧取得（検索・ソート対応）"""
    attr_types = UserService.get_attribute_types()
    rows = UserService.get_all(sort=sort, order=order, q=q)

    tbody = ""
    for r in rows:
        user_attrs = UserService.get_attributes(r['id'])
        tbody += render_row(r, attr_types=attr_types, user_attrs=user_attrs)

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
def create(cd: str = Form(...), name: str = Form(...), email: str = Form(...)):
    attr_types = UserService.get_attribute_types()
    u = UserService.create(cd=cd, name=name, email=email)
    return HTMLResponse(render_row(u, attr_types=attr_types, user_attrs={}))


@router.put("/{id}", response_class=HTMLResponse)
async def update(id: int, request: Request, cd: str = Form(...), name: str = Form(...), email: str = Form(...)):
    attr_types = UserService.get_attribute_types()

    # ユーザー更新
    u = UserService.update(user_id=id, cd=cd, name=name, email=email)
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
