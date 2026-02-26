"""アサイン管理グリッドレンダラー

責務: アサイン管理グリッドのHTML生成のみ
4階層構造: project-row → issue-row → task-row → assignee-sub-row
担当者0〜1名: task-row内で直接表示、2名以上: サブ行展開
"""
from html import escape

from .renders import render_row_label, render_task_status_cell, render_issue_status_cell, render_estimate_cell, render_plan_cell, render_progress_cell


def _calc_weighted_progress(assignee_data: list[tuple]) -> int | None:
    """山積計による加重平均の進捗率を計算

    assignee_data: [(progress_rate, plan_total), ...]
    山積計が全て0の場合は単純平均にフォールバック
    """
    with_progress = [(pr, pt) for pr, pt in assignee_data if pr is not None]
    if not with_progress:
        return None
    total_weight = sum(pt for _, pt in with_progress)
    if total_weight > 0:
        return round(sum(pr * pt for pr, pt in with_progress) / total_weight)
    return round(sum(pr for pr, _ in with_progress) / len(with_progress))


def _render_grid_header(months: list[str]) -> str:
    """グリッドヘッダー行を生成"""
    month_headers = ""
    for ym in months:
        month_num = int(ym.split("-")[1])
        month_headers += f'<th class="date-header" data-year-month="{ym}">{month_num}月</th>'

    return f'''<tr>
        <th class="row-header">作業</th>
        <th class="user-header">担当</th>
        <th class="status-header">状態</th>
        <th class="estimate-header">見積</th>
        <th class="actual-header">実績</th>
        <th class="remaining-header">理論残</th>
        <th class="progress-header">完了%</th>
        <th class="actual-remaining-header">実際残</th>
        <th class="schedule-diff-header">予定差</th>
        <th class="plan-total-header">山積計</th>
        <th class="unallocated-header">未割当</th>
        {month_headers}
    </tr>'''


def _fmt_hours(val: float) -> str:
    """工数表示フォーマット（見積・実績共用）"""
    return f"{val:.2f}h" if val > 0 else "-"


def _fmt_remaining(estimate: float, actual: float) -> str:
    """理論残表示フォーマット（見積−実績）"""
    if estimate == 0 and actual == 0:
        return '-', ''
    remaining = estimate - actual
    css = ' remaining-negative' if remaining < 0 else ''
    return f"{remaining:.2f}h", css


def _render_month_summary_cells(months: list[str], month_totals: dict) -> str:
    """月別集計セルを生成（プロジェクト・案件・マルチ担当タスク用）"""
    cells = ''
    for ym in months:
        val = month_totals.get(ym, 0)
        display = f"{val:.2f}" if val > 0 else "-"
        cells += f'<td class="summary-cell">{display}</td>'
    return cells


def _fmt_unallocated(val: float | None) -> tuple[str, str]:
    """未割当表示フォーマット（実際残−山積計）"""
    if val is None:
        return '-', ''
    css = ' unallocated-negative' if val < 0 else ''
    return f'{val:.2f}h', css


def _fmt_schedule_diff(val: float) -> tuple[str, str]:
    """予定差表示フォーマット（山積計−理論残）"""
    css = ' schedule-diff-negative' if val < 0 else ''
    return f'{val:.2f}h', css


def _render_project_row(row: dict, months: list[str], estimate_total: float = 0,
                        actual_total: float = 0, month_totals: dict = None,
                        plan_total: float = 0,
                        actual_remaining_total: float | None = None,
                        unallocated_total: float | None = None) -> str:
    """プロジェクト集計行を生成"""
    pid = row['project_id']
    cells = _render_month_summary_cells(months, month_totals or {})
    remaining_text, remaining_css = _fmt_remaining(estimate_total, actual_total)
    ar_display = f'{actual_remaining_total:.2f}h' if actual_remaining_total is not None else '-'
    sd_display, sd_css = _fmt_schedule_diff(plan_total - (estimate_total - actual_total))
    ua_display, ua_css = _fmt_unallocated(unallocated_total)

    return (
        f'<tr class="project-row" data-project-id="{pid}">'
        f'<td class="project-name">'
        f'<span class="toggle-icon" onclick="toggleProject({pid})">▼</span> {escape(row["project_name"])}'
        f'</td>'
        f'<td></td>'
        f'<td></td>'
        f'<td class="summary-cell estimate-summary">{_fmt_hours(estimate_total)}</td>'
        f'<td class="summary-cell actual-summary">{_fmt_hours(actual_total)}</td>'
        f'<td class="summary-cell remaining-summary{remaining_css}">{remaining_text}</td>'
        f'<td></td>'
        f'<td class="summary-cell actual-remaining-summary">{ar_display}</td>'
        f'<td class="summary-cell schedule-diff-summary{sd_css}">{sd_display}</td>'
        f'<td class="summary-cell plan-total-summary">{_fmt_hours(plan_total)}</td>'
        f'<td class="summary-cell unallocated-summary{ua_css}">{ua_display}</td>'
        f'{cells}'
        f'</tr>'
    )


def _render_issue_row(row: dict, months: list[str], status_labels: dict = None,
                      estimate_total: float = 0, actual_total: float = 0,
                      month_totals: dict = None, plan_total: float = 0,
                      actual_remaining_total: float | None = None,
                      unallocated_total: float | None = None) -> str:
    """案件集計行を生成"""
    pid = row['project_id']
    iid = row['issue_id']
    cells = _render_month_summary_cells(months, month_totals or {})
    issue_status_cell = render_issue_status_cell(iid, row.get('issue_status', 'open'), status_labels or {})

    remaining_text, remaining_css = _fmt_remaining(estimate_total, actual_total)
    ar_display = f'{actual_remaining_total:.2f}h' if actual_remaining_total is not None else '-'
    sd_display, sd_css = _fmt_schedule_diff(plan_total - (estimate_total - actual_total))
    ua_display, ua_css = _fmt_unallocated(unallocated_total)

    return (
        f'<tr class="issue-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<td class="issue-name">'
        f'<span class="toggle-icon" onclick="toggleIssue({pid}, {iid})">▼</span> {escape(row["issue_cd"])} {escape(row["issue_name"])}'
        f'</td>'
        f'<td></td>'
        f'{issue_status_cell}'
        f'<td class="summary-cell estimate-summary">{_fmt_hours(estimate_total)}</td>'
        f'<td class="summary-cell actual-summary">{_fmt_hours(actual_total)}</td>'
        f'<td class="summary-cell remaining-summary{remaining_css}">{remaining_text}</td>'
        f'<td></td>'
        f'<td class="summary-cell actual-remaining-summary">{ar_display}</td>'
        f'<td class="summary-cell schedule-diff-summary{sd_css}">{sd_display}</td>'
        f'<td class="summary-cell plan-total-summary">{_fmt_hours(plan_total)}</td>'
        f'<td class="summary-cell unallocated-summary{ua_css}">{ua_display}</td>'
        f'{cells}'
        f'</tr>'
    )


def _render_tag_badges(tags: list[dict]) -> str:
    """タグバッジHTML生成（グリッド用小サイズ）"""
    if not tags:
        return ""
    badges = " ".join(
        f'<span class="tag-badge tag-badge-sm" style="background:{escape(t["color"] or "#6b7280")}">{escape(t["name"])}</span>'
        for t in tags
    )
    return f' <span class="row-tags">{badges}</span>'


def _render_autocomplete_input(task_id: int) -> str:
    """オートコンプリート入力欄HTML"""
    return (
        f'<div class="assignee-autocomplete-wrapper">'
        f'<input type="text" class="autocomplete-input assignee-autocomplete-input" '
        f'placeholder="ユーザーを検索..." autocomplete="off" '
        f'data-task-id="{task_id}" '
        f'oninput="searchAssignees(this, {task_id})" '
        f'onfocus="searchAssignees(this, {task_id})" '
        f'onblur="hideAssigneeAutocomplete(this)">'
        f'<div class="autocomplete-dropdown assignee-autocomplete-dropdown"></div>'
        f'</div>'
    )


def _render_task_row(row: dict, months: list[str], task_tags: list[dict],
                     task_status_labels: dict, assignee_count: int,
                     first_assignee: dict = None, plans: dict = None,
                     task_month_totals: dict = None,
                     plan_total: float = 0,
                     weighted_progress: int | None = None,
                     actual_remaining: float | None = None,
                     unallocated: float | None = None) -> str:
    """作業行を生成（4階層の3段目）

    担当者数に応じて担当列の内容を変える:
    - 0名: オートコンプリート入力欄（直接割当可能）
    - 1名: ユーザー名表示（サブ行なし）
    - 2名以上: バッジ表示（サブ行あり）
    +/−ボタンは作業列の右端に配置
    """
    pid = row['project_id']
    iid = row['issue_id']
    tid = row['task_id']
    # 月セル: 担当者数に応じて切り替え
    hidden_plan = 0.0
    if assignee_count == 1 and first_assignee:
        uid = first_assignee['user_id']
        cells = ''.join(
            render_plan_cell(tid, uid, ym, (plans or {}).get((tid, uid, ym), 0))
            for ym in months
        )
        visible_plan_sum = sum((plans or {}).get((tid, uid, ym), 0) for ym in months)
        hidden_plan = plan_total - visible_plan_sum
    elif assignee_count >= 2:
        cells = _render_month_summary_cells(months, task_month_totals or {})
    else:
        cells = ''.join(f'<td class="log-cell"></td>' for _ in months)
    tag_html = _render_tag_badges(task_tags or [])
    status_cell = render_task_status_cell(tid, row.get('task_status', 'open'), task_status_labels or {})
    estimate_cell = render_estimate_cell(tid, row.get('estimate_hours'))
    actual_val = row.get('actual_hours') or 0
    actual_display = f'{actual_val:.2f}h' if actual_val > 0 else '-'
    actual_cell = f'<td class="actual-cell">{actual_display}</td>'
    est_val = row.get('estimate_hours') or 0
    remaining_text, remaining_css = _fmt_remaining(est_val, actual_val)
    remaining_cell = f'<td class="remaining-cell{remaining_css}">{remaining_text}</td>'

    # 完了%セル: 1名→入力欄、2名以上→加重平均表示、0名→空
    if assignee_count == 1 and first_assignee:
        progress_cell = render_progress_cell(first_assignee['assignee_id'], row.get('progress_rate'))
    elif assignee_count >= 2 and weighted_progress is not None:
        progress_cell = f'<td class="progress-cell weighted-progress">{weighted_progress}%</td>'
    else:
        progress_cell = '<td></td>'

    # 予定差セル: 山積計 − 理論残
    sd_display, sd_css = _fmt_schedule_diff(plan_total - (est_val - actual_val))

    # 未割当セル: 実際残 − 山積計
    ua_display, ua_css = _fmt_unallocated(unallocated)

    # 作業列: +ボタン（常時）、−ボタン（1名の場合のみ）
    plus_btn = (
        f' <button type="button" class="btn-add-assignee"'
        f' onclick="addAssigneeRow({tid})" title="担当行を追加">＋</button>'
    )
    minus_btn = ''
    if assignee_count == 1 and first_assignee:
        minus_btn = (
            f' <button type="button" class="btn-remove-assignee"'
            f' onclick="removeTaskAssignee(this)" title="担当を外す">−</button>'
        )

    # 担当列の内容
    assignee_attr = ''
    if assignee_count == 0:
        assignee_html = _render_autocomplete_input(tid)
    elif assignee_count == 1 and first_assignee:
        aid = first_assignee['assignee_id']
        uname = escape(first_assignee['user_name'])
        assignee_html = f'<span class="assignee-display">{uname}</span>'
        assignee_attr = f' data-assignee-id="{aid}"'
    else:
        count_class = 'assignee-count-badge'
        assignee_html = f'<span class="{count_class}">{assignee_count}名</span>'

    return (
        f'<tr class="task-row" data-project-id="{pid}" data-issue-id="{iid}" data-task-id="{tid}"{assignee_attr}>'
        f'<td class="task-label">'
        f'<div class="task-label-flex">'
        f'<span class="task-label-content">'
        f'<span class="toggle-icon" onclick="toggleTask({pid}, {iid}, {tid})">▼</span> '
        f'{render_row_label(row["task_name"])}{tag_html}'
        f'</span>'
        f'<span class="task-actions">{plus_btn}{minus_btn}</span>'
        f'</div>'
        f'</td>'
        f'<td class="assignee-count-cell">{assignee_html}</td>'
        f'{status_cell}'
        f'{estimate_cell}'
        f'{actual_cell}'
        f'{remaining_cell}'
        f'{progress_cell}'
        f'<td class="actual-remaining-cell">{f"{actual_remaining:.2f}h" if actual_remaining is not None else "-"}</td>'
        f'<td class="schedule-diff-cell{sd_css}">{sd_display}</td>'
        f'<td class="summary-cell plan-total-summary" data-hidden-plan="{hidden_plan:.2f}">{_fmt_hours(plan_total)}</td>'
        f'<td class="unallocated-cell{ua_css}">{ua_display}</td>'
        f'{cells}'
        f'</tr>'
    )


def _render_assignee_sub_row(row: dict, months: list[str], plans: dict = None,
                             plan_total: float = 0) -> str:
    """担当者サブ行を生成（4階層の4段目、2名以上の場合のみ使用）
    −ボタンは作業列（assignee-indent）に配置"""
    pid = row['project_id']
    iid = row['issue_id']
    tid = row['task_id']
    assignee_id = row.get('assignee_id')
    uid = row.get('user_id')
    if uid:
        cells = ''.join(
            render_plan_cell(tid, uid, ym, (plans or {}).get((tid, uid, ym), 0))
            for ym in months
        )
        visible_plan_sum = sum((plans or {}).get((tid, uid, ym), 0) for ym in months)
    else:
        cells = ''.join(f'<td class="log-cell"></td>' for _ in months)
        visible_plan_sum = 0
    hidden_plan = plan_total - visible_plan_sum
    user_display = escape(row['user_name']) if row.get('user_name') else ''

    assignee_attr = f' data-assignee-id="{assignee_id}"' if assignee_id else ''
    remove_btn = (
        '<button type="button" class="btn-remove-assignee"'
        ' onclick="removeAssigneeRow(this)" title="担当行を削除">−</button>'
    )

    # 完了%セル
    progress_cell = render_progress_cell(assignee_id, row.get('progress_rate')) if assignee_id else '<td></td>'

    return (
        f'<tr class="assignee-sub-row" data-project-id="{pid}" data-issue-id="{iid}" data-task-id="{tid}"{assignee_attr}>'
        f'<td class="assignee-indent">{remove_btn}</td>'
        f'<td class="assignee-name-cell"><span class="assignee-display">{user_display}</span></td>'
        f'<td></td>'
        f'<td></td>'
        f'<td></td>'
        f'<td></td>'
        f'{progress_cell}'
        f'<td></td>'
        f'<td></td>'
        f'<td class="summary-cell plan-total-summary" data-hidden-plan="{hidden_plan:.2f}">{_fmt_hours(plan_total)}</td>'
        f'<td></td>'
        f'{cells}'
        f'</tr>'
    )


def render_assignment_grid(months: list[str], rows: list[dict], tags_map: dict = None,
                           status_labels_map: dict = None, task_status_labels_map: dict = None,
                           plans: dict = None, plan_totals: dict = None) -> str:
    """アサイン管理グリッドHTML生成"""
    if tags_map is None:
        tags_map = {}
    if status_labels_map is None:
        status_labels_map = {}
    if task_status_labels_map is None:
        task_status_labels_map = {}
    if not rows:
        return '<p class="empty-message">表示する行がありません。担当割当を行ってください。</p>'

    # 一括操作ボタン
    bulk_actions = '''<div class="bulk-actions">
        <button type="button" class="btn btn-ghost btn-sm" onclick="expandAll()">全て展開</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="collapseAll()">全て折り畳み</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="collapseToIssues()">案件のみ表示</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="collapseToTasks()">作業のみ表示</button>
    </div>'''

    header = _render_grid_header(months)

    # 事前スキャン: タスクごとの担当者情報
    task_info: dict[int, dict] = {}
    for row in rows:
        tid = row['task_id']
        if tid not in task_info:
            task_info[tid] = {'count': 0, 'first': None}
        if row.get('user_id') is not None:
            task_info[tid]['count'] += 1
            if task_info[tid]['first'] is None:
                task_info[tid]['first'] = {
                    'assignee_id': row.get('assignee_id'),
                    'user_id': row.get('user_id'),
                    'user_name': row.get('user_name'),
                }

    # 事前スキャン: タスクごとの担当者進捗データ（加重平均用）
    task_assignee_progress: dict[int, list[tuple]] = {}
    for row in rows:
        tid = row['task_id']
        if row.get('user_id') is not None:
            uid = row['user_id']
            pr = row.get('progress_rate')
            pt = plan_totals.get((tid, uid), 0)
            task_assignee_progress.setdefault(tid, []).append((pr, pt))

    # 事前スキャン: 見積・実績工数集計 + 実際残（プロジェクト・案件・タスク別）
    project_estimate: dict[int, float] = {}
    issue_estimate: dict[int, float] = {}
    project_actual: dict[int, float] = {}
    issue_actual: dict[int, float] = {}
    task_actual_remaining: dict[int, float | None] = {}
    project_actual_remaining: dict[int, float] = {}
    issue_actual_remaining: dict[int, float] = {}
    seen_tasks: set[int] = set()
    for row in rows:
        tid = row['task_id']
        if tid in seen_tasks:
            continue
        seen_tasks.add(tid)
        pid = row['project_id']
        iid = row['issue_id']
        est = row.get('estimate_hours') or 0
        act = row.get('actual_hours') or 0
        project_estimate[pid] = project_estimate.get(pid, 0) + est
        issue_estimate[iid] = issue_estimate.get(iid, 0) + est
        project_actual[pid] = project_actual.get(pid, 0) + act
        issue_actual[iid] = issue_actual.get(iid, 0) + act
        # 実際残: 見積×(1−完了%/100)、完了%未入力は除外
        progress = _calc_weighted_progress(task_assignee_progress.get(tid, []))
        if est > 0 and progress is not None:
            ar = est * (1 - progress / 100)
            task_actual_remaining[tid] = ar
            project_actual_remaining[pid] = project_actual_remaining.get(pid, 0) + ar
            issue_actual_remaining[iid] = issue_actual_remaining.get(iid, 0) + ar
        else:
            task_actual_remaining[tid] = None

    # 事前スキャン: 山積計（全月合計、プロジェクト・案件・タスク別）
    plan_totals = plan_totals or {}
    project_plan_total: dict[int, float] = {}
    issue_plan_total: dict[int, float] = {}
    task_plan_total: dict[int, float] = {}
    for (t_id, u_id), total in plan_totals.items():
        if total <= 0:
            continue
        for r in rows:
            if r['task_id'] == t_id:
                p_id = r['project_id']
                i_id = r['issue_id']
                project_plan_total[p_id] = project_plan_total.get(p_id, 0) + total
                issue_plan_total[i_id] = issue_plan_total.get(i_id, 0) + total
                task_plan_total[t_id] = task_plan_total.get(t_id, 0) + total
                break

    # 事前スキャン: 未割当（実際残 − 山積計、実際残がないタスクは除外）
    task_unallocated: dict[int, float | None] = {}
    project_unallocated: dict[int, float] = {}
    issue_unallocated: dict[int, float] = {}
    seen_tasks_ua: set[int] = set()
    for row in rows:
        tid = row['task_id']
        if tid in seen_tasks_ua:
            continue
        seen_tasks_ua.add(tid)
        ar = task_actual_remaining.get(tid)
        if ar is not None:
            ua = ar - task_plan_total.get(tid, 0)
            task_unallocated[tid] = ua
            pid = row['project_id']
            iid = row['issue_id']
            project_unallocated[pid] = project_unallocated.get(pid, 0) + ua
            issue_unallocated[iid] = issue_unallocated.get(iid, 0) + ua
        else:
            task_unallocated[tid] = None

    # 事前スキャン: 月別計画工数集計（プロジェクト・案件・タスク別）
    plans = plans or {}
    project_month_totals: dict[int, dict[str, float]] = {}
    issue_month_totals: dict[int, dict[str, float]] = {}
    task_month_totals: dict[int, dict[str, float]] = {}
    for (t_id, u_id, ym), hours in plans.items():
        if hours <= 0:
            continue
        # タスク→案件→プロジェクトの紐付けを取得するためrow走査
        for r in rows:
            if r['task_id'] == t_id:
                p_id = r['project_id']
                i_id = r['issue_id']
                project_month_totals.setdefault(p_id, {})
                project_month_totals[p_id][ym] = project_month_totals[p_id].get(ym, 0) + hours
                issue_month_totals.setdefault(i_id, {})
                issue_month_totals[i_id][ym] = issue_month_totals[i_id].get(ym, 0) + hours
                task_month_totals.setdefault(t_id, {})
                task_month_totals[t_id][ym] = task_month_totals[t_id].get(ym, 0) + hours
                break

    html_rows = []
    current_project_id = None
    current_issue_id = None
    current_task_id = None

    for row in rows:
        pid = row['project_id']
        iid = row['issue_id']
        tid = row['task_id']

        # プロジェクトヘッダー
        if pid != current_project_id:
            current_project_id = pid
            current_issue_id = None
            current_task_id = None
            html_rows.append(_render_project_row(row, months, project_estimate.get(pid, 0), project_actual.get(pid, 0), project_month_totals.get(pid, {}), project_plan_total.get(pid, 0), project_actual_remaining.get(pid), project_unallocated.get(pid)))

        # 案件ヘッダー
        if iid != current_issue_id:
            current_issue_id = iid
            current_task_id = None
            html_rows.append(_render_issue_row(row, months, status_labels_map.get(pid, {}), issue_estimate.get(iid, 0), issue_actual.get(iid, 0), issue_month_totals.get(iid, {}), issue_plan_total.get(iid, 0), issue_actual_remaining.get(iid), issue_unallocated.get(iid)))

        # 作業ヘッダー
        if tid != current_task_id:
            current_task_id = tid
            task_tags = tags_map.get(tid, [])
            info = task_info.get(tid, {'count': 0, 'first': None})
            wp = _calc_weighted_progress(task_assignee_progress.get(tid, []))
            html_rows.append(_render_task_row(
                row, months, task_tags,
                task_status_labels_map.get(iid, {}),
                info['count'], info['first'], plans,
                task_month_totals.get(tid, {}),
                task_plan_total.get(tid, 0),
                wp,
                task_actual_remaining.get(tid),
                task_unallocated.get(tid)
            ))

        # 担当者サブ行（2名以上の場合のみ）
        if row.get('user_id') is not None:
            info = task_info.get(tid, {'count': 0})
            if info['count'] >= 2:
                sub_plan_total = plan_totals.get((tid, row.get('user_id')), 0)
                html_rows.append(_render_assignee_sub_row(row, months, plans, sub_plan_total))

    return f'{bulk_actions}<table class="log-table"><thead>{header}</thead><tbody>{"".join(html_rows)}</tbody></table>'
