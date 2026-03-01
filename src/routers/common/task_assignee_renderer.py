"""担当割当マトリクスのHTML生成

責務: 担当割当画面のマトリクス部品（ヘッダー・案件行・作業行）を生成
renders.py と同パターンのプレゼンテーション専用モジュール
"""
from html import escape


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
