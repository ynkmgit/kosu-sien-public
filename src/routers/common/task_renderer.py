"""作業一覧のHTML生成

責務: 作業CRUD画面のテーブル部品（ヘッダー・行・集計行）を生成
renders.py と同パターンのプレゼンテーション専用モジュール
"""
from html import escape

from .renders import render_edit_actions, TAG_DEFAULT_COLOR


def fmt_hours(val) -> str:
    """工数表示フォーマット"""
    if val is None:
        return "-"
    return f"{float(val):.1f}"


def render_status_select(current: str, task_id: int, project_id: int, issue_id: int, status_labels: dict):
    """作業ステータスセレクトボックス生成"""
    options = "".join(
        f'<option value="{s}" {"selected" if s == current else ""}>{label}</option>'
        for s, label in status_labels.items()
    )
    return f'''<select class="status-select status-{current}"
        hx-put="/projects/{project_id}/issues/{issue_id}/tasks/{task_id}/status"
        hx-target="#task-{task_id}"
        hx-swap="outerHTML"
        name="status">{options}</select>'''


def render_tag_badges(tags: list[dict]) -> str:
    """タグバッジHTML生成"""
    if not tags:
        return ""
    return " ".join(
        f'<span class="tag-badge" style="background:{escape(t["color"] or TAG_DEFAULT_COLOR)}">{escape(t["name"])}</span>'
        for t in tags
    )


def render_tag_checkboxes(all_tags: list[dict], task_tags: list[dict], task_id: int, project_id: int, issue_id: int) -> str:
    """編集モード用タグチェックボックス生成"""
    if not all_tags:
        return '<span class="text-muted">タグなし</span>'
    task_tag_ids = {t['id'] for t in task_tags}
    items = []
    for tag in all_tags:
        checked = "checked" if tag['id'] in task_tag_ids else ""
        items.append(
            f'<label class="tag-checkbox"><input type="checkbox" value="{tag["id"]}" {checked}'
            f' hx-put="/projects/{project_id}/issues/{issue_id}/tasks/{task_id}/tags/{tag["id"]}"'
            f' hx-target="#task-{task_id}" hx-swap="outerHTML">'
            f'<span class="tag-badge tag-badge-sm" style="background:{escape(tag["color"] or TAG_DEFAULT_COLOR)}">{escape(tag["name"])}</span></label>'
        )
    return " ".join(items)


def render_thead(project_id: int, issue_id: int):
    """テーブルヘッダー生成"""
    return """<tr>
        <th class="col-cd">CD</th>
        <th class="col-name">作業名</th>
        <th class="col-sort">ステータス</th>
        <th>タグ</th>
        <th class="col-value">計画</th>
        <th class="col-value">実績</th>
        <th class="col-sort">進捗</th>
        <th class="col-actions-sm">操作</th>
    </tr>"""


def render_row(t, project_id: int, issue_id: int, status_labels: dict = None,
               task_tags: list[dict] = None, all_tags: list[dict] = None, editing=False):
    """作業行HTML生成"""
    cd = escape(t['cd'] or '')
    name = escape(t['name'])
    status = t.get('status') or 'open'
    plan = t.get('estimate_hours')
    actual = t.get('actual_hours', 0) or 0
    progress = t.get('progress_rate') or 0
    tags = task_tags or []

    base_path = f"/projects/{project_id}/issues/{issue_id}/tasks"

    if editing:
        plan_val = f"{plan:.1f}" if plan else ""
        status_options = ""
        if status_labels:
            status_options = "".join(
                f'<option value="{s}" {"selected" if s == status else ""}>{label}</option>'
                for s, label in status_labels.items()
            )
        tag_html = render_tag_checkboxes(all_tags or [], tags, t['id'], project_id, issue_id)
        return f"""
        <tr id="task-{t['id']}" class="editing-row">
            <td><input type="text" name="cd" value="{cd}" class="edit-input input-cd-narrow"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><select name="status" class="edit-input">{status_options}</select></td>
            <td>{tag_html}</td>
            <td><input type="number" name="estimate_hours" value="{plan_val}" step="0.25" min="0" class="edit-input input-hours"></td>
            <td class="value-cell">{fmt_hours(actual)}</td>
            <td>{progress}%</td>
            <td>{render_edit_actions("task", t['id'], base_path)}</td>
        </tr>"""

    status_select = render_status_select(status, t['id'], project_id, issue_id, status_labels or {})
    tag_badges = render_tag_badges(tags)
    return f"""
    <tr id="task-{t['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell">{name}</td>
        <td>{status_select}</td>
        <td>{tag_badges}</td>
        <td class="value-cell">{fmt_hours(plan)}</td>
        <td class="value-cell">{fmt_hours(actual)}</td>
        <td><span class="progress-badge">{progress}%</span></td>
        <td><div class="actions-cell">
            <button hx-get="{base_path}/{t['id']}/edit" hx-target="#task-{t['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


def render_totals_row(totals: dict):
    """集計行HTML生成"""
    return f"""
    <tr class="subtotal-row">
        <td colspan="4" class="totals-label">合計</td>
        <td class="value-cell"><strong>{fmt_hours(totals['internal_plan_total'])}</strong></td>
        <td class="value-cell"><strong>{fmt_hours(totals['actual_total'])}</strong></td>
        <td colspan="2"></td>
    </tr>"""


def parse_hours(value: str) -> float | None:
    """工数入力パース（空文字はNone、負の値はエラー）"""
    if not value or value.strip() == "":
        return None
    hours = float(value)
    if hours < 0:
        raise ValueError("工数は0以上の値を入力してください")
    return hours
