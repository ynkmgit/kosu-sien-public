"""レンダリング部品

責務: グリッドUI、CRUDアクション、テーブルヘッダーのHTML生成
"""
from html import escape


# === グリッドUI部品 ===

def render_log_cell(task_id: int, user_id: int, date_str: str, hours: float, extra_classes: str = "") -> str:
    """工数入力セルHTML生成"""
    hours_display = f"{hours:.2f}" if hours > 0 else ""
    cell_class = f"log-cell{extra_classes}"
    return f'''<td class="{cell_class}">
        <input type="number" class="log-input" step="0.25" min="0.25"
               value="{hours_display}"
               data-task-id="{task_id}"
               data-user-id="{user_id}"
               data-date="{date_str}"
               hx-post="/work-logs"
               hx-trigger="change"
               hx-vals='js:{{task_id: event.target.dataset.taskId, user_id: event.target.dataset.userId, work_date: event.target.dataset.date, hours: event.target.value || 0}}'
               hx-swap="none">
    </td>'''


def render_progress_cell(task_id: int, progress_rate) -> str:
    """進捗率入力セルHTML生成"""
    progress_display = str(progress_rate) if progress_rate is not None else ""
    return f'''<td class="progress-cell">
        <input type="number" class="progress-input" step="1" min="0" max="100"
               value="{progress_display}"
               placeholder="-"
               data-task-id="{task_id}"
               hx-put="/tasks/{task_id}/progress"
               hx-trigger="change"
               hx-vals='js:{{progress_rate: event.target.value}}'
               hx-swap="none">
    </td>'''


def render_row_label(issue_name: str, task_name: str, user_name: str) -> str:
    """行ラベルHTML生成"""
    return f"├─ {escape(issue_name)}/{escape(task_name)} ({escape(user_name)})"


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
