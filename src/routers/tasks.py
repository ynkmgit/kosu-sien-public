"""作業CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はTaskServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import TaskService, TaskStatusService, IssueTagService, TaskTagService
from .common import templates, get_project_or_404, get_issue_or_404, render_edit_actions, render_sortable_th, FilterParams, get_filter_params

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/tasks", tags=["tasks"])


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
        f'<span class="tag-badge" style="background:{escape(t["color"] or "#6b7280")}">{escape(t["name"])}</span>'
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
            f'<span class="tag-badge tag-badge-sm" style="background:{escape(tag["color"] or "#6b7280")}">{escape(tag["name"])}</span></label>'
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


@router.get("", response_class=HTMLResponse)
def page(request: Request, project_id: int, issue_id: int, filters: FilterParams = Depends(get_filter_params)):
    proj = get_project_or_404(project_id)
    iss = get_issue_or_404(project_id, issue_id)
    totals = TaskService.get_issue_totals(issue_id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    return templates.TemplateResponse(request, "tasks.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "totals": totals,
        "status_labels": status_labels,
        "filter_params": filters.to_dict(),
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int):
    """作業一覧取得"""
    get_issue_or_404(project_id, issue_id)
    rows = TaskService.get_all_with_actuals(issue_id)
    totals = TaskService.get_issue_totals(issue_id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    all_tags = IssueTagService.get_all(issue_id)
    tags_map = TaskTagService.get_task_tags_map(issue_id)
    tbody = "".join(
        render_row(r, project_id, issue_id, status_labels,
                   task_tags=tags_map.get(r['id'], []), all_tags=all_tags)
        for r in rows
    )
    tbody += render_totals_row(totals)
    thead = render_thead(project_id, issue_id)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id_with_actuals(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id_with_actuals(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags, editing=True))


def parse_hours(value: str) -> float | None:
    """工数入力パース（空文字はNone、負の値はエラー）"""
    if not value or value.strip() == "":
        return None
    hours = float(value)
    if hours < 0:
        raise ValueError("工数は0以上の値を入力してください")
    return hours


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int,
           cd: str = Form(...),
           name: str = Form(...),
           estimate_hours: str = Form(""),
           status: str = Form("open")):
    get_issue_or_404(project_id, issue_id)
    try:
        t = TaskService.create(
            issue_id=issue_id,
            cd=cd,
            name=name,
            estimate_hours=parse_hours(estimate_hours),
            status=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # actual_hoursを追加（新規なので0）
    t['actual_hours'] = 0
    status_labels = TaskStatusService.get_status_labels(issue_id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=[], all_tags=all_tags))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int,
           cd: str = Form(...),
           name: str = Form(...),
           estimate_hours: str = Form(""),
           status: str = Form("open")):
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        TaskService.update(
            task_id=id,
            cd=cd,
            name=name,
            estimate_hours=parse_hours(estimate_hours),
            status=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 実績付きで再取得
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.put("/{id}/status", response_class=HTMLResponse)
def update_status(project_id: int, issue_id: int, id: int, status: str = Form(...)):
    """ステータスのみ更新"""
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskService.update_status(id, status)
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.put("/{id}/tags/{tag_id}", response_class=HTMLResponse)
def toggle_tag(project_id: int, issue_id: int, id: int, tag_id: int):
    """タグ付与/解除トグル"""
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskTagService.toggle(id, tag_id)
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskService.delete(id)
    return HTMLResponse("")


# 作業インライン更新用ルーター（/tasks/{id}/estimate, /tasks/{id}/status）
task_progress_router = APIRouter(prefix="/tasks", tags=["task_progress"])


@task_progress_router.put("/{task_id}/estimate", response_class=HTMLResponse)
def update_estimate_inline(task_id: int, estimate_hours: str = Form(default="")):
    """見積工数更新（グリッドインライン編集用）"""
    value = parse_hours(estimate_hours) if estimate_hours else None
    try:
        if not TaskService.update_estimate(task_id, value):
            raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return HTMLResponse("")


@task_progress_router.put("/{task_id}/status", response_class=HTMLResponse)
def update_task_status_light(task_id: int, status: str = Form(...)):
    """作業ステータス軽量更新（グリッド用）"""
    if not TaskService.update_status(task_id, status):
        raise HTTPException(status_code=404, detail="Task not found")
    return HTMLResponse("")
