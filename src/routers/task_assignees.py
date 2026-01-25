"""担当割当CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はTaskAssigneeServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import TaskAssigneeService, UserService
from .common import templates, get_project_or_404

router = APIRouter(prefix="/projects/{project_id}/assignees", tags=["task_assignees"])


def render_matrix(project_id: int, users, tasks, assignments):
    """マトリクスHTML生成"""
    if not users:
        return '<p class="empty-message">有効なユーザーがいません</p>'
    if not tasks:
        return '<p class="empty-message">作業がありません。先に案件と作業を登録してください。</p>'

    # ヘッダー行
    header_cells = "".join(
        f'<th class="user-header">{escape(u["cd"])}</th>' for u in users
    )
    header = f'<tr><th class="task-header">案件 / 作業</th>{header_cells}</tr>'

    # 案件ごとにグループ化
    rows = []
    current_issue_id = None
    issue_user_counts = {}  # 案件ごとのユーザー別担当数

    for task in tasks:
        # 新しい案件の開始
        if task['issue_id'] != current_issue_id:
            # 前の案件の集約行を出力
            if current_issue_id is not None:
                rows.append(_render_issue_row(
                    current_issue_id, current_issue_cd, current_issue_name,
                    users, issue_user_counts
                ))
            # 新しい案件の初期化
            current_issue_id = task['issue_id']
            current_issue_cd = task['issue_cd']
            current_issue_name = task['issue_name']
            issue_user_counts = {u['id']: 0 for u in users}

        # 作業行
        rows.append(_render_task_row(project_id, task, users, assignments, issue_user_counts))

    # 最後の案件の集約行
    if current_issue_id is not None:
        rows.append(_render_issue_row(
            current_issue_id, current_issue_cd, current_issue_name,
            users, issue_user_counts
        ))

    # 案件行を適切な位置に挿入（作業行の前に）
    sorted_rows = _sort_rows_with_issue_headers(rows)

    tbody = "".join(sorted_rows)
    return f'<table class="matrix-table"><thead>{header}</thead><tbody>{tbody}</tbody></table>'


def _render_issue_row(issue_id, issue_cd, issue_name, users, user_counts):
    """案件集約行を生成"""
    cells = []
    for u in users:
        count = user_counts.get(u['id'], 0)
        display = f"({count})" if count > 0 else "-"
        cells.append(f'<td class="issue-cell">{display}</td>')

    return {
        'type': 'issue',
        'issue_id': issue_id,
        'html': f'''<tr class="issue-row">
            <td class="issue-name">{escape(issue_cd)} {escape(issue_name)}</td>
            {"".join(cells)}
        </tr>'''
    }


def _render_task_row(project_id, task, users, assignments, issue_user_counts):
    """作業行を生成"""
    cells = []
    for u in users:
        is_assigned = (task['id'], u['id']) in assignments
        if is_assigned:
            issue_user_counts[u['id']] = issue_user_counts.get(u['id'], 0) + 1

        cell_class = "assigned" if is_assigned else ""
        symbol = "●" if is_assigned else ""
        cells.append(f'''<td class="task-cell {cell_class}"
            hx-post="/projects/{project_id}/assignees/toggle"
            hx-vals='{{"task_id": {task["id"]}, "user_id": {u["id"]}}}'
            hx-target="#matrix-container"
            hx-swap="innerHTML">{symbol}</td>''')

    return {
        'type': 'task',
        'issue_id': task['issue_id'],
        'html': f'''<tr class="task-row">
            <td class="task-name">├─ {escape(task["cd"])} {escape(task["name"])}</td>
            {"".join(cells)}
        </tr>'''
    }


def _sort_rows_with_issue_headers(rows):
    """行を案件ヘッダー→作業の順にソート"""
    # issue_id でグループ化
    grouped = {}
    for row in rows:
        issue_id = row['issue_id']
        if issue_id not in grouped:
            grouped[issue_id] = {'issue': None, 'tasks': []}
        if row['type'] == 'issue':
            grouped[issue_id]['issue'] = row['html']
        else:
            grouped[issue_id]['tasks'].append(row['html'])

    # 順序を維持しながら結合
    result = []
    seen_issues = set()
    for row in rows:
        issue_id = row['issue_id']
        if issue_id not in seen_issues:
            seen_issues.add(issue_id)
            if grouped[issue_id]['issue']:
                result.append(grouped[issue_id]['issue'])
            result.extend(grouped[issue_id]['tasks'])

    return result


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
    return templates.TemplateResponse(request, "task_assignees.html", {
        "active": "projects",
        "project": proj,
        "filter_params": filter_params,
    })


@router.get("/matrix", response_class=HTMLResponse)
def get_matrix(project_id: int):
    """マトリクス取得"""
    get_project_or_404(project_id)
    users = UserService.get_active_list()
    tasks = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assignments = TaskAssigneeService.get_all_assignments(project_id)
    return HTMLResponse(render_matrix(project_id, users, tasks, assignments))


@router.post("/toggle", response_class=HTMLResponse)
def toggle_assignment(project_id: int, task_id: int = Form(...), user_id: int = Form(...)):
    """担当割当のトグル"""
    get_project_or_404(project_id)

    # 作業の存在確認とプロジェクト所属確認
    task = TaskAssigneeService.get_task_in_project(task_id, project_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ユーザーの存在確認と有効確認
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 既存の割当を確認
    existing = TaskAssigneeService.get_assignment(task_id, user_id)

    if existing:
        # 割当解除
        TaskAssigneeService.delete(existing['id'])
    else:
        # 新規割当（無効ユーザーはブロック）
        if user['is_active'] == 0:
            raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")
        TaskAssigneeService.create(task_id, user_id)

    # マトリクス再取得
    users = UserService.get_active_list()
    tasks = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assignments = TaskAssigneeService.get_all_assignments(project_id)

    return HTMLResponse(render_matrix(project_id, users, tasks, assignments))


@router.post("", response_class=HTMLResponse)
def create_assignment(project_id: int, task_id: int = Form(...), user_id: int = Form(...)):
    """担当割当追加"""
    get_project_or_404(project_id)

    # 作業の存在確認
    task = TaskAssigneeService.get_task_in_project(task_id, project_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # ユーザーの存在確認と有効確認
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")

    # 既存チェック（既にあれば何もしない）
    existing = TaskAssigneeService.get_assignment(task_id, user_id)
    if not existing:
        TaskAssigneeService.create(task_id, user_id)

    return HTMLResponse("")


@router.delete("/{id}", response_class=HTMLResponse)
def delete_assignment(project_id: int, id: int):
    """担当割当解除"""
    get_project_or_404(project_id)

    # 割当の存在確認とプロジェクト所属確認
    assignment = TaskAssigneeService.get_assignment_in_project(id, project_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    TaskAssigneeService.delete(id)
    return HTMLResponse("")
