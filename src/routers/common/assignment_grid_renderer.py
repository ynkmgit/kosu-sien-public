"""アサイン管理グリッドレンダラー

責務: アサイン管理グリッドのHTML生成のみ
4階層構造: project-row → issue-row → task-row → assignee-sub-row
担当者0〜1名: task-row内で直接表示、2名以上: サブ行展開
集計ロジックはAssignmentAggregationServiceに委譲
"""
from html import escape

from services.assignment_aggregation_service import AssignmentAggregationService, calc_weighted_progress

from .renders import render_row_label, render_tag_badges, render_task_status_cell, render_issue_status_cell, render_estimate_cell, render_plan_cell, render_progress_cell


def _render_grid_header(months: list[str]) -> str:
    """グリッドヘッダー行を生成"""
    month_headers = "".join(
        f'<div class="gc date-header" data-year-month="{ym}">{int(ym.split("-")[1])}月</div>'
        for ym in months
    )

    return f'''<div class="grid-row grid-header">
        <div class="gc gc-frozen row-header">作業</div>
        <div class="gc user-header">担当</div>
        <div class="gc status-header">状態</div>
        <div class="gc estimate-header">見積</div>
        <div class="gc actual-header">実績</div>
        <div class="gc remaining-header">理論残</div>
        <div class="gc progress-header">完了%</div>
        <div class="gc actual-remaining-header">実際残</div>
        <div class="gc schedule-diff-header">予定差</div>
        <div class="gc plan-total-header">山積計</div>
        <div class="gc unallocated-header">未割当</div>
        {month_headers}
    </div>'''


def _fmt_hours(val: float) -> str:
    """工数表示フォーマット（見積・実績共用）"""
    return f"{val:.2f}h" if val > 0 else "-"


def _fmt_remaining(estimate: float, actual: float) -> tuple[str, str]:
    """理論残表示フォーマット（見積−実績）"""
    if estimate == 0 and actual == 0:
        return '-', ''
    remaining = estimate - actual
    attr = ' data-negative' if remaining < 0 else ''
    return f"{remaining:.2f}h", attr


def _render_month_summary_cells(months: list[str], month_totals: dict) -> str:
    """月別集計セルを生成（プロジェクト・案件・マルチ担当タスク用）"""
    return "".join(
        f'<div class="gc summary-cell numeric">{f"{val:.2f}" if val > 0 else "-"}</div>'
        for ym in months
        for val in [month_totals.get(ym, 0)]
    )


def _fmt_unallocated(val: float | None) -> tuple[str, str]:
    """未割当表示フォーマット（実際残−山積計）"""
    if val is None:
        return '-', ''
    attr = ' data-negative' if val < 0 else ''
    return f'{val:.2f}h', attr


def _fmt_schedule_diff(val: float) -> tuple[str, str]:
    """予定差表示フォーマット（山積計−理論残）"""
    attr = ' data-negative' if val < 0 else ''
    return f'{val:.2f}h', attr


def _render_project_row(row: dict, months: list[str], estimate_total: float = 0,
                        actual_total: float = 0, month_totals: dict = None,
                        plan_total: float = 0,
                        actual_remaining_total: float | None = None,
                        unallocated_total: float | None = None) -> str:
    """プロジェクト集計行を生成"""
    pid = row['project_id']
    cells = _render_month_summary_cells(months, month_totals or {})
    remaining_text, remaining_attr = _fmt_remaining(estimate_total, actual_total)
    ar_display = f'{actual_remaining_total:.2f}h' if actual_remaining_total is not None else '-'
    sd_display, sd_attr = _fmt_schedule_diff(plan_total - (estimate_total - actual_total))
    ua_display, ua_attr = _fmt_unallocated(unallocated_total)

    return (
        f'<div class="grid-row project-row" data-project-id="{pid}">'
        f'<div class="gc gc-frozen project-name">'
        f'<span class="toggle-icon" onclick="toggleProject({pid})">▼</span> {escape(row["project_name"])}'
        f'</div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc summary-cell estimate-summary numeric">{_fmt_hours(estimate_total)}</div>'
        f'<div class="gc summary-cell actual-summary numeric">{_fmt_hours(actual_total)}</div>'
        f'<div class="gc summary-cell remaining-summary numeric"{remaining_attr}>{remaining_text}</div>'
        f'<div class="gc"></div>'
        f'<div class="gc summary-cell actual-remaining-summary numeric">{ar_display}</div>'
        f'<div class="gc summary-cell schedule-diff-summary numeric"{sd_attr}>{sd_display}</div>'
        f'<div class="gc summary-cell plan-total-summary numeric">{_fmt_hours(plan_total)}</div>'
        f'<div class="gc summary-cell unallocated-summary numeric"{ua_attr}>{ua_display}</div>'
        f'{cells}'
        f'</div>'
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

    remaining_text, remaining_attr = _fmt_remaining(estimate_total, actual_total)
    ar_display = f'{actual_remaining_total:.2f}h' if actual_remaining_total is not None else '-'
    sd_display, sd_attr = _fmt_schedule_diff(plan_total - (estimate_total - actual_total))
    ua_display, ua_attr = _fmt_unallocated(unallocated_total)

    return (
        f'<div class="grid-row issue-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<div class="gc gc-frozen issue-name">'
        f'<span class="toggle-icon" onclick="toggleIssue({pid}, {iid})">▼</span> {escape(row["issue_cd"])} {escape(row["issue_name"])}'
        f'</div>'
        f'<div class="gc"></div>'
        f'{issue_status_cell}'
        f'<div class="gc summary-cell estimate-summary numeric">{_fmt_hours(estimate_total)}</div>'
        f'<div class="gc summary-cell actual-summary numeric">{_fmt_hours(actual_total)}</div>'
        f'<div class="gc summary-cell remaining-summary numeric"{remaining_attr}>{remaining_text}</div>'
        f'<div class="gc"></div>'
        f'<div class="gc summary-cell actual-remaining-summary numeric">{ar_display}</div>'
        f'<div class="gc summary-cell schedule-diff-summary numeric"{sd_attr}>{sd_display}</div>'
        f'<div class="gc summary-cell plan-total-summary numeric">{_fmt_hours(plan_total)}</div>'
        f'<div class="gc summary-cell unallocated-summary numeric"{ua_attr}>{ua_display}</div>'
        f'{cells}'
        f'</div>'
    )


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
                     unallocated: float | None = None,
                     multi_hidden_plan: float = 0.0) -> str:
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
        hidden_plan = multi_hidden_plan
    else:
        cells = ''.join(f'<div class="gc log-cell"></div>' for _ in months)
    tag_html = render_tag_badges(task_tags or [])
    status_cell = render_task_status_cell(tid, row.get('task_status', 'open'), task_status_labels or {})
    estimate_cell = render_estimate_cell(tid, row.get('estimate_hours'))
    actual_val = row.get('actual_hours') or 0
    actual_display = f'{actual_val:.2f}h' if actual_val > 0 else '-'
    actual_cell = f'<div class="gc actual-cell numeric">{actual_display}</div>'
    est_val = row.get('estimate_hours') or 0
    remaining_text, remaining_attr = _fmt_remaining(est_val, actual_val)
    remaining_cell = f'<div class="gc remaining-cell numeric"{remaining_attr}>{remaining_text}</div>'

    # 完了%セル: 1名→入力欄、2名以上→加重平均表示、0名→空
    if assignee_count == 1 and first_assignee:
        progress_cell = render_progress_cell(first_assignee['assignee_id'], row.get('progress_rate'))
    elif assignee_count >= 2 and weighted_progress is not None:
        progress_cell = f'<div class="gc progress-cell numeric" data-weighted>{weighted_progress}%</div>'
    else:
        progress_cell = '<div class="gc"></div>'

    # 予定差セル: 山積計 − 理論残
    sd_display, sd_attr = _fmt_schedule_diff(plan_total - (est_val - actual_val))

    # 未割当セル: 実際残 − 山積計
    ua_display, ua_attr = _fmt_unallocated(unallocated)

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
        f'<div class="grid-row task-row" data-project-id="{pid}" data-issue-id="{iid}" data-task-id="{tid}"{assignee_attr}>'
        f'<div class="gc gc-frozen task-label">'
        f'<div class="task-label-flex">'
        f'<span class="task-label-content">'
        f'<span class="toggle-icon" onclick="toggleTask({pid}, {iid}, {tid})">▼</span> '
        f'{render_row_label(row["task_name"])}{tag_html}'
        f'</span>'
        f'<span class="task-actions">{plus_btn}{minus_btn}</span>'
        f'</div>'
        f'</div>'
        f'<div class="gc assignee-count-cell">{assignee_html}</div>'
        f'{status_cell}'
        f'{estimate_cell}'
        f'{actual_cell}'
        f'{remaining_cell}'
        f'{progress_cell}'
        f'<div class="gc actual-remaining-cell numeric">{f"{actual_remaining:.2f}h" if actual_remaining is not None else "-"}</div>'
        f'<div class="gc schedule-diff-cell numeric"{sd_attr}>{sd_display}</div>'
        f'<div class="gc summary-cell plan-total-summary numeric" data-hidden-plan="{hidden_plan:.2f}">{_fmt_hours(plan_total)}</div>'
        f'<div class="gc unallocated-cell numeric"{ua_attr}>{ua_display}</div>'
        f'{cells}'
        f'</div>'
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
        cells = ''.join(f'<div class="gc log-cell"></div>' for _ in months)
        visible_plan_sum = 0
    hidden_plan = plan_total - visible_plan_sum
    user_display = escape(row['user_name']) if row.get('user_name') else ''

    assignee_attr = f' data-assignee-id="{assignee_id}"' if assignee_id else ''
    remove_btn = (
        '<button type="button" class="btn-remove-assignee"'
        ' onclick="removeAssigneeRow(this)" title="担当行を削除">−</button>'
    )

    # 完了%セル
    progress_cell = render_progress_cell(assignee_id, row.get('progress_rate')) if assignee_id else '<div class="gc"></div>'

    return (
        f'<div class="grid-row assignee-sub-row" data-project-id="{pid}" data-issue-id="{iid}" data-task-id="{tid}"{assignee_attr}>'
        f'<div class="gc gc-frozen assignee-indent">{remove_btn}</div>'
        f'<div class="gc assignee-name-cell"><span class="assignee-display">{user_display}</span></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'{progress_cell}'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc summary-cell plan-total-summary numeric" data-hidden-plan="{hidden_plan:.2f}">{_fmt_hours(plan_total)}</div>'
        f'<div class="gc"></div>'
        f'{cells}'
        f'</div>'
    )


def render_task_block(rows: list[dict], months: list[str], plans: dict = None,
                      plan_totals: dict = None, tags_map: dict = None,
                      task_status_labels: dict = None) -> str:
    """単一タスクの task-row + サブ行群を返す

    Args:
        rows: 同一 task_id の行データリスト（get_assignee_rows の結果をフィルタ済み）
        months: YYYY-MM リスト
        plans: {(task_id, user_id, year_month): hours}
        plan_totals: {(task_id, user_id): total_hours}
        tags_map: {task_id: [{id, name, color}, ...]}
        task_status_labels: {status_code: label}
    """
    if not rows:
        return ''
    plans = plans or {}
    plan_totals = plan_totals or {}
    tags_map = tags_map or {}
    task_status_labels = task_status_labels or {}

    agg = AssignmentAggregationService.prescan(rows, plans, plan_totals)
    row = rows[0]
    tid = row['task_id']

    task_tags = tags_map.get(tid, [])
    info = agg.task_info.get(tid, {'count': 0, 'first': None})
    wp = calc_weighted_progress(agg.task_assignee_progress.get(tid, []))
    html_parts = [_render_task_row(
        row, months, task_tags, task_status_labels,
        info['count'], info['first'], plans,
        agg.task_month_totals.get(tid, {}),
        agg.task_plan_total.get(tid, 0),
        wp,
        agg.task_actual_remaining.get(tid),
        agg.task_unallocated.get(tid),
        agg.task_hidden_plan.get(tid, 0.0)
    )]

    if info['count'] >= 2:
        for r in rows:
            if r.get('user_id') is not None:
                sub_plan_total = plan_totals.get((tid, r['user_id']), 0)
                html_parts.append(_render_assignee_sub_row(r, months, plans, sub_plan_total))

    return ''.join(html_parts)


def render_empty_sub_row(task_id: int, project_id: int, issue_id: int, months: list[str]) -> str:
    """空の担当者サブ行を返す（＋ボタンで追加用）"""
    cells = ''.join(f'<div class="gc log-cell"></div>' for _ in months)
    remove_btn = (
        '<button type="button" class="btn-remove-assignee"'
        ' onclick="removeAssigneeRow(this)" title="担当行を削除">−</button>'
    )
    autocomplete = (
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
    return (
        f'<div class="grid-row assignee-sub-row" data-project-id="{project_id}" data-issue-id="{issue_id}" data-task-id="{task_id}">'
        f'<div class="gc gc-frozen assignee-indent">{remove_btn}</div>'
        f'<div class="gc assignee-name-cell">{autocomplete}</div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc summary-cell plan-total-summary numeric" data-hidden-plan="0.00">-</div>'
        f'<div class="gc"></div>'
        f'{cells}'
        f'</div>'
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

    plans = plans or {}
    plan_totals = plan_totals or {}
    agg = AssignmentAggregationService.prescan(rows, plans, plan_totals)

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
            html_rows.append(_render_project_row(row, months, agg.project_estimate.get(pid, 0), agg.project_actual.get(pid, 0), agg.project_month_totals.get(pid, {}), agg.project_plan_total.get(pid, 0), agg.project_actual_remaining.get(pid), agg.project_unallocated.get(pid)))

        # 案件ヘッダー
        if iid != current_issue_id:
            current_issue_id = iid
            current_task_id = None
            html_rows.append(_render_issue_row(row, months, status_labels_map.get(pid, {}), agg.issue_estimate.get(iid, 0), agg.issue_actual.get(iid, 0), agg.issue_month_totals.get(iid, {}), agg.issue_plan_total.get(iid, 0), agg.issue_actual_remaining.get(iid), agg.issue_unallocated.get(iid)))

        # 作業ヘッダー
        if tid != current_task_id:
            current_task_id = tid
            task_tags = tags_map.get(tid, [])
            info = agg.task_info.get(tid, {'count': 0, 'first': None})
            wp = calc_weighted_progress(agg.task_assignee_progress.get(tid, []))
            html_rows.append(_render_task_row(
                row, months, task_tags,
                task_status_labels_map.get(iid, {}),
                info['count'], info['first'], plans,
                agg.task_month_totals.get(tid, {}),
                agg.task_plan_total.get(tid, 0),
                wp,
                agg.task_actual_remaining.get(tid),
                agg.task_unallocated.get(tid),
                agg.task_hidden_plan.get(tid, 0.0)
            ))

        # 担当者サブ行（2名以上の場合のみ）
        if row.get('user_id') is not None:
            info = agg.task_info.get(tid, {'count': 0})
            if info['count'] >= 2:
                sub_plan_total = plan_totals.get((tid, row.get('user_id')), 0)
                html_rows.append(_render_assignee_sub_row(row, months, plans, sub_plan_total))

    num_months = len(months)
    grid_cols = f"minmax(180px, 1fr) 120px 80px 70px 70px 70px 70px 70px 70px 70px 70px repeat({num_months}, 70px)"
    return f'{bulk_actions}<div class="grid" style="--grid-cols: {grid_cols}">{header}{"".join(html_rows)}</div>'
