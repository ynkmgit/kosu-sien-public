"""レンダリング部品

責務: グリッドUI、CRUDアクション、テーブルヘッダーのHTML生成
"""
from html import escape

TAG_DEFAULT_COLOR = "#6b7280"

# === グリッドUI部品 ===

def render_log_cell(task_id: int, user_id: int, date_str: str, hours: float, extra_classes: str = "") -> str:
    """工数入力セルHTML生成（click-to-edit: テキスト表示、クリックでinput生成）"""
    hours_display = f"{hours:.2f}" if hours > 0 else ""
    cell_class = f"gc log-cell numeric{extra_classes}"
    return (f'<div class="{cell_class}"'
            f' data-task-id="{task_id}"'
            f' data-user-id="{user_id}"'
            f' data-date="{date_str}">{hours_display}</div>')


def render_progress_cell(assignee_id: int, progress_rate) -> str:
    """進捗率セルHTML生成（click-to-edit: テキスト表示、クリックでinput生成）"""
    progress_display = f"{progress_rate}%" if progress_rate is not None else ""
    return (f'<div class="gc progress-cell numeric"'
            f' data-assignee-id="{assignee_id}"'
            f' data-value="{progress_rate if progress_rate is not None else ""}">{progress_display}</div>')


def render_estimate_cell(task_id: int, estimate_hours) -> str:
    """見積工数セルHTML生成（click-to-edit: テキスト表示、クリックでinput生成）"""
    display = f"{float(estimate_hours):.2f}" if estimate_hours else ""
    return (f'<div class="gc estimate-cell numeric"'
            f' data-task-id="{task_id}"'
            f' data-value="{display}">{display}</div>')


def render_plan_cell(task_id: int, user_id: int, year_month: str, hours: float) -> str:
    """月次計画入力セルHTML生成（空セルはinputなしで軽量化）"""
    if hours > 0:
        return f'''<div class="gc plan-cell numeric">
            <input type="number" class="plan-input" step="0.25" min="0"
                   value="{hours:.2f}"
                   data-task-id="{task_id}"
                   data-user-id="{user_id}"
                   data-year-month="{year_month}">
        </div>'''
    return (f'<div class="gc plan-cell plan-cell-empty numeric"'
            f' data-task-id="{task_id}"'
            f' data-user-id="{user_id}"'
            f' data-year-month="{year_month}"></div>')


def render_tag_badges(tags: list[dict]) -> str:
    """タグバッジHTML生成（グリッド用小サイズ）"""
    if not tags:
        return ""
    badges = " ".join(
        f'<span class="tag-badge tag-badge-sm" style="background:{escape(t["color"] or TAG_DEFAULT_COLOR)}">{escape(t["name"])}</span>'
        for t in tags
    )
    return f' <span class="row-tags">{badges}</span>'


def render_row_label(task_name: str) -> str:
    """行ラベルHTML生成"""
    return f"├─ {escape(task_name)}"


def render_user_cell(user_name: str) -> str:
    """担当者セルHTML生成"""
    return f'<div class="gc user-cell">{escape(user_name)}</div>'


def _render_status_cell(entity_id: int, current_status: str, status_labels: dict,
                        id_attr: str, action: str) -> str:
    """ステータスセルHTML生成（click-to-edit: テキスト表示、クリックでselect生成）"""
    import json as _json
    current = current_status or 'open'
    label = escape(status_labels.get(current, current))
    labels_json = escape(_json.dumps(status_labels, ensure_ascii=False))
    return (f'<div class="gc status-cell status-{current}"'
            f' data-{id_attr}="{entity_id}"'
            f' data-action="{action}"'
            f' data-status="{current}"'
            f' data-labels="{labels_json}">{label}</div>')


def render_task_status_cell(task_id: int, current_status: str, status_labels: dict) -> str:
    """作業ステータスセレクトセルHTML生成（グリッド用）"""
    return _render_status_cell(task_id, current_status, status_labels, "task-id", "task-status")


def render_issue_status_cell(issue_id: int, current_status: str, status_labels: dict) -> str:
    """案件ステータスセレクトセルHTML生成（グリッド用）"""
    return _render_status_cell(issue_id, current_status, status_labels, "issue-id", "issue-status")


# === CRUDアクション部品 ===

def render_edit_actions(entity: str, id: int, base_path: str) -> str:
    """編集モードのCRUDアクションボタン生成

    Args:
        entity: エンティティ名（project, task, issue等）
        id: エンティティID
        base_path: APIベースパス（例: /projects, /projects/1/issues）

    Returns:
        アクションボタンHTML（保存・取消・削除）
    """
    return f'''<div class="actions-cell">
        <button hx-put="{base_path}/{id}" hx-include="closest tr" hx-target="#{entity}-{id}" hx-swap="outerHTML" class="btn btn-sm btn-success">保存</button>
        <button hx-get="{base_path}/{id}/row" hx-target="#{entity}-{id}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">取消</button>
        <button hx-delete="{base_path}/{id}" hx-target="#{entity}-{id}" hx-swap="outerHTML" hx-confirm="削除しますか？" class="btn btn-sm btn-danger">削除</button>
    </div>'''


# === テーブルヘッダー部品 ===

def render_sortable_th(name: str, label: str, sort: str, order: str,
                       list_endpoint: str, target_id: str,
                       css_class: str = None) -> str:
    """ソート可能なテーブルヘッダーセルを生成

    Args:
        name: カラム名（ソートキー）
        label: 表示ラベル
        sort: 現在のソート列
        order: 現在のソート順（asc/desc）
        list_endpoint: リストエンドポイント（例: /projects/list）
        target_id: HTMXターゲットID（例: project-table）
        css_class: 列幅用CSSクラス（オプション、例: col-cd）

    Returns:
        <th>要素HTML
    """
    next_order = "desc" if sort == name and order == "asc" else "asc"
    icon = "▼" if sort == name and order == "desc" else "▲"
    active = "active" if sort == name else ""
    classes = f"{css_class} sortable" if css_class else "sortable"
    return f'<th class="{classes}" hx-get="{list_endpoint}?sort={name}&order={next_order}" hx-target="#{target_id}" hx-swap="innerHTML" hx-include="[name=\'q\']">{label}<span class="sort-icon {active}">{icon}</span></th>'
