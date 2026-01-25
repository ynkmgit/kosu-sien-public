"""案件CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はIssueServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import IssueService
from .common import templates, get_project_or_404, get_rate_class, render_edit_actions, render_sortable_th

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["issues"])


def render_status_select(current: str, issue_id: int, project_id: int, status_labels: dict):
    """ステータスセレクトボックス生成"""
    options = "".join(
        f'<option value="{s}" {"selected" if s == current else ""}>{label}</option>'
        for s, label in status_labels.items()
    )
    return f'''<select class="status-select status-{current}"
        hx-put="/projects/{project_id}/issues/{issue_id}/status"
        hx-target="#issue-{issue_id}"
        hx-swap="outerHTML"
        name="status">{options}</select>'''


def render_thead(sort: str, order: str, project_id: int):
    """ソート状態を反映したテーブルヘッダー生成"""
    endpoint = f"/projects/{project_id}/issues/list"
    def col(name, label, css_class=None):
        return render_sortable_th(name, label, sort, order, endpoint, "issue-table", css_class)

    return f"""<tr>
        {col("cd", "CD", "col-cd")}
        {col("name", "案件名", "col-name")}
        {col("status", "ステータス", "col-sort")}
        <th class="col-rate">見積</th>
        <th class="col-rate">実績</th>
        <th class="col-rate">残</th>
        <th class="col-rate">消化率</th>
        {col("description", "説明")}
        <th class="col-name">操作</th>
    </tr>"""


def format_comparison_display(comp: dict) -> tuple[str, str, str, str]:
    """比較データを表示用文字列にフォーマット（HTML生成のみ）

    Args:
        comp: IssueService.calculate_comparison()の戻り値

    Returns:
        (見積表示, 実績表示, 残表示, 消化率表示) のタプル
    """
    estimate = comp['estimate']
    actual = comp['actual']
    remaining = comp['remaining']
    rate = comp['rate']

    estimate_display = f"{estimate:.1f}h" if estimate > 0 else "-"
    actual_display = f"{actual:.1f}h" if actual > 0 else "-"

    if estimate > 0:
        remaining_display = f"{remaining:.1f}h"
        # 残がマイナスの場合はtext-dangerクラス
        if comp['is_overrun']:
            remaining_display = f'<span class="text-danger">{remaining_display}</span>'
        # 消化率は段階的警告
        rate_class = get_rate_class(rate)
        rate_display = f'<span class="{rate_class}">{rate:.0f}%</span>'
    else:
        remaining_display = "-"
        rate_display = "-"

    return estimate_display, actual_display, remaining_display, rate_display


def render_row(i, project_id: int, status_labels: dict, estimate_total: float = 0, actual_total: float = 0, editing=False):
    """案件行HTML生成"""
    cd = escape(i['cd'] or '')
    name = escape(i['name'])
    desc = escape(i['description'] or '')
    status = i['status'] or 'open'
    comp = IssueService.calculate_comparison(estimate_total, actual_total)
    estimate_display, actual_display, remaining_display, rate_display = format_comparison_display(comp)

    if editing:
        status_options = "".join(
            f'<option value="{s}" {"selected" if s == status else ""}>{label}</option>'
            for s, label in status_labels.items()
        )
        base_path = f"/projects/{project_id}/issues"
        return f"""
        <tr id="issue-{i['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="cd" value="{cd}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><select name="status" class="edit-input">{status_options}</select></td>
            <td class="col-rate">{estimate_display}</td>
            <td class="col-rate">{actual_display}</td>
            <td class="col-rate">{remaining_display}</td>
            <td class="col-rate">{rate_display}</td>
            <td><input type="text" name="description" value="{desc}" class="edit-input"></td>
            <td>{render_edit_actions("issue", i['id'], base_path)}</td>
        </tr>"""

    status_select = render_status_select(status, i['id'], project_id, status_labels)
    return f"""
    <tr id="issue-{i['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell">{name}</td>
        <td>{status_select}</td>
        <td class="col-rate">{estimate_display}</td>
        <td class="col-rate">{actual_display}</td>
        <td class="col-rate">{remaining_display}</td>
        <td class="col-rate">{rate_display}</td>
        <td class="desc-cell">{desc}</td>
        <td><div class="actions-cell">
            <a href="/projects/{project_id}/issues/{i['id']}/estimates" class="btn btn-sm btn-ghost">見積</a>
            <a href="/projects/{project_id}/issues/{i['id']}/tasks" class="btn btn-sm btn-ghost">作業</a>
            <button hx-get="/projects/{project_id}/issues/{i['id']}/edit" hx-target="#issue-{i['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    project_id: int,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    proj = get_project_or_404(project_id)
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "issues.html", {
        "active": "projects",
        "project": proj,
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, sort: str = "cd", order: str = "asc", q: str = ""):
    """案件一覧取得（検索・ソート対応）"""
    get_project_or_404(project_id)
    # 1クエリで案件+見積合計+実績合計を取得
    rows = IssueService.get_all_with_totals(project_id=project_id, sort=sort, order=order, q=q)
    status_labels = IssueService.get_status_labels(project_id)
    tbody = "".join(render_row(r, project_id, status_labels, r['estimate_total'], r['actual_total']) for r in rows)
    thead = render_thead(sort, order, project_id)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, id: int):
    get_project_or_404(project_id)
    i = IssueService.get_by_id(id)
    if not i or i['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, id: int):
    get_project_or_404(project_id)
    i = IssueService.get_by_id(id)
    if not i or i['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, cd: str = Form(...), name: str = Form(...), status: str = Form("open"), description: str = Form("")):
    get_project_or_404(project_id)
    i = IssueService.create(project_id=project_id, cd=cd, name=name, status=status, description=description)
    status_labels = IssueService.get_status_labels(project_id)
    return HTMLResponse(render_row(i, project_id, status_labels, 0))  # 新規作成時は見積0


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, id: int, cd: str = Form(...), name: str = Form(...), status: str = Form("open"), description: str = Form("")):
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    i = IssueService.update(issue_id=id, cd=cd, name=name, status=status, description=description)
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.put("/{id}/status", response_class=HTMLResponse)
def update_status(project_id: int, id: int, status: str = Form(...)):
    """ステータスのみ更新"""
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    # 既存の値を保持してステータスのみ更新
    i = IssueService.update(issue_id=id, cd=existing['cd'], name=existing['name'], status=status, description=existing['description'] or "")
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, id: int):
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    IssueService.delete(id)
    return HTMLResponse("")
