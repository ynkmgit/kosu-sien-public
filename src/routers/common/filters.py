"""フィルターUI部品

責務: フィルター関連のHTML生成 + ステータス収集
"""
from datetime import datetime
from html import escape

from services import StatusService, TaskStatusService


def render_filter_tags(items, selected_ids: list[int], type_name: str) -> str:
    """選択済みアイテムのタグHTML生成"""
    tags = ""
    for item in items:
        if item['id'] in selected_ids:
            tags += f'''<span class="filter-tag" data-type="{type_name}" data-id="{item['id']}">
                {escape(item['name'])}
                <button type="button" class="tag-remove" onclick="removeFilter('{type_name}', {item['id']})">×</button>
            </span>'''
    return tags


def render_filter_options(items, selected_ids: list[int]) -> str:
    """未選択アイテムのselect option HTML生成"""
    return "".join(
        f'<option value="{item["id"]}">{escape(item["cd"])} {escape(item["name"])}</option>'
        for item in items if item['id'] not in selected_ids
    )


def render_filter_group(label: str, tags: str, options: str, type_name: str) -> str:
    """フィルターグループHTML生成（従来のドロップダウン方式）"""
    return f'''<div class="filter-group">
        <label class="filter-label">{label}</label>
        <div class="filter-tags">{tags}</div>
        <select class="filter-select" onchange="addFilter('{type_name}', this.value)">
            <option value="">+ 追加...</option>
            {options}
        </select>
    </div>'''


def render_autocomplete_filter_group(label: str, tags: str, type_name: str, placeholder: str = "検索...") -> str:
    """オートコンプリート付きフィルターグループHTML生成"""
    return f'''<div class="filter-group">
        <label class="filter-label">{label}</label>
        <div class="filter-tags">{tags}</div>
        <div class="autocomplete-wrapper">
            <input type="text" class="autocomplete-input" data-type="{type_name}"
                   placeholder="{placeholder}" autocomplete="off"
                   oninput="handleAutocomplete(this, '{type_name}')"
                   onfocus="handleAutocomplete(this, '{type_name}')"
                   onblur="setTimeout(() => hideAutocomplete('{type_name}'), 200)">
            <div class="autocomplete-dropdown" id="autocomplete-{type_name}"></div>
        </div>
    </div>'''


def render_exclude_done_toggles(exclude_done_issue: bool, exclude_done_task: bool) -> str:
    """完了除外トグルHTML生成（案件・作業別）"""
    issue_checked = "checked" if exclude_done_issue else ""
    task_checked = "checked" if exclude_done_task else ""
    return f'''<div class="filter-group">
        <label class="filter-label">完了除外</label>
        <label class="exclude-done-check">
            <input type="checkbox" {issue_checked} onchange="toggleExcludeDoneIssue()">
            <span class="exclude-done-label">案件</span>
        </label>
        <label class="exclude-done-check">
            <input type="checkbox" {task_checked} onchange="toggleExcludeDoneTask()">
            <span class="exclude-done-label">作業</span>
        </label>
    </div>'''


def _collect_unique_statuses(items: list[dict], get_all_fn) -> list[dict]:
    """ステータスを収集（code重複排除、ID付き）"""
    item_ids = [item['id'] for item in items]
    all_statuses = get_all_fn(item_ids)
    seen = set()
    result = []
    for item_id in item_ids:
        for s in all_statuses.get(item_id, []):
            if s['code'] not in seen:
                seen.add(s['code'])
                result.append({'id': s['id'], 'name': s['name']})
    return result


def collect_unique_issue_statuses(projects: list[dict]) -> list[dict]:
    """全プロジェクトの案件ステータスを収集（code重複排除、ID付き）"""
    return _collect_unique_statuses(projects, StatusService.get_all_bulk)


def collect_unique_task_statuses(issues: list[dict]) -> list[dict]:
    """全案件の作業ステータスを収集（code重複排除、ID付き）"""
    return _collect_unique_statuses(issues, TaskStatusService.get_all_bulk)


def render_common_filter_groups(users, projects, issues, tags,
                                 selected_users: list[int], selected_projects: list[int],
                                 selected_issues: list[int], selected_tags: list[int],
                                 issue_statuses: list[dict], task_statuses_all: list[dict],
                                 selected_issue_statuses: list[int], selected_task_statuses: list[int],
                                 exclude_done_issue: bool, exclude_done_task: bool) -> str:
    """6種フィルター + 完了除外（日付・表示切替を含まない共通部分）"""
    user_group = render_autocomplete_filter_group(
        "ユーザー", render_filter_tags(users, selected_users, "user"), "user", "ユーザーを検索..."
    )
    project_group = render_autocomplete_filter_group(
        "プロジェクト", render_filter_tags(projects, selected_projects, "project"), "project", "プロジェクトを検索..."
    )
    issue_group = render_autocomplete_filter_group(
        "案件", render_filter_tags(issues, selected_issues, "issue"), "issue", "案件を検索..."
    )
    tag_group = render_autocomplete_filter_group(
        "タグ", render_filter_tags(tags, selected_tags, "tag"), "tag", "タグを検索..."
    )
    issue_status_group = render_autocomplete_filter_group(
        "案件状態", render_filter_tags(issue_statuses, selected_issue_statuses, "issue_status"), "issue_status", "案件状態を検索..."
    )
    task_status_group = render_autocomplete_filter_group(
        "作業状態", render_filter_tags(task_statuses_all, selected_task_statuses, "task_status"), "task_status", "作業状態を検索..."
    )
    exclude_done_group = render_exclude_done_toggles(exclude_done_issue, exclude_done_task)
    return f"{user_group}{project_group}{issue_group}{tag_group}{issue_status_group}{task_status_group}{exclude_done_group}"


def render_assignment_month_nav(base_month: str = None) -> str:
    """アサイン管理の月ナビゲーション生成"""
    now = datetime.now()
    if base_month:
        year, month = int(base_month[:4]), int(base_month[5:7])
    else:
        year, month = now.year, now.month

    prev_m, prev_y = month - 1, year
    if prev_m < 1:
        prev_m, prev_y = 12, year - 1
    next_m, next_y = month + 1, year
    if next_m > 12:
        next_m, next_y = 1, year + 1

    prev_ym = f"{prev_y}-{prev_m:02d}"
    next_ym = f"{next_y}-{next_m:02d}"
    display = f"{year}年{month}月 〜"

    return f'''<div class="filter-group">
        <label class="filter-label">基準月</label>
        <div class="week-nav">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeBaseMonth('{prev_ym}')">◀</button>
            <span class="week-range">{display}</span>
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeBaseMonth('{next_ym}')">▶</button>
            <button type="button" class="btn btn-ghost btn-sm ml-sm" onclick="changeBaseMonth('')">当月</button>
        </div>
    </div>'''


def render_view_toggle(current_view: str) -> str:
    """表示切替ボタンHTML生成"""
    week_class = "btn-primary" if current_view == "week" else "btn-ghost"
    month_class = "btn-primary" if current_view == "month" else "btn-ghost"
    return f'''<div class="view-toggle">
        <a href="javascript:void(0)" onclick="changeView('week')" class="btn {week_class} btn-sm">週</a>
        <a href="javascript:void(0)" onclick="changeView('month')" class="btn {month_class} btn-sm">月</a>
    </div>'''
