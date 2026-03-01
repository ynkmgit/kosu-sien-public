"""ユーザー一覧のHTML生成

責務: ユーザーCRUD画面のテーブル部品（ヘッダー・行）を生成
renders.py と同パターンのプレゼンテーション専用モジュール
"""
from html import escape

from .renders import render_edit_actions, render_sortable_th


def render_thead(sort: str, order: str, attr_types: list):
    """ソート状態を反映したテーブルヘッダー生成"""
    def col(name, label, css_class=None):
        return render_sortable_th(name, label, sort, order, "/users/list", "user-table", css_class)

    # 属性列のヘッダー
    attr_headers = "".join(f'<th class="col-code">{escape(t["name"])}</th>' for t in attr_types)

    return f"""<tr>
        {col("cd", "CD", "col-cd")}
        {col("name", "名前", "col-name")}
        {attr_headers}
        <th class="col-actions">操作</th>
    </tr>"""


def render_row(u, editing=False, attr_types=None, user_attrs=None):
    """ユーザー行HTML生成"""
    cd = escape(u['cd'] or '')
    name = escape(u['name'])

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
        <tr id="user-{u['id']}" class="editing-row">
            <td><input type="text" name="cd" value="{cd}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            {attr_cells_html}
            <td>{render_edit_actions("user", u['id'], "/users")}</td>
        </tr>"""
    return f"""
    <tr id="user-{u['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell">{name}</td>
        {attr_cells_html}
        <td><div class="actions-cell">
            <button hx-get="/users/{u['id']}/edit" hx-target="#user-{u['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""
