"""グリッドデータ取得ヘルパー

責務: グリッド表示に必要なマスタデータ・フィルター・メタデータの一括取得
work_logs.py と assignments.py の共通パターンを集約
"""
from dataclasses import dataclass

from services import (
    UserService, ProjectService, IssueService,
    WorkLogService, TaskTagService, IssueTagService,
    StatusService, TaskStatusService,
)
from .filter_params import FilterParams
from .filters import collect_unique_issue_statuses, collect_unique_task_statuses


@dataclass
class GridContext:
    """グリッド表示用コンテキスト"""
    users: list[dict]
    projects: list[dict]
    issues: list[dict]
    all_tags: list[dict]
    issue_statuses: list[dict]
    task_statuses_all: list[dict]
    rows: list[dict]
    tags_map: dict
    status_labels_map: dict
    task_status_labels_map: dict


def load_grid_context(filters: FilterParams, include_unassigned: bool = False) -> GridContext:
    """グリッド表示に必要な全データを一括取得"""
    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    issues = IssueService.get_list()
    all_tags = IssueTagService.get_list()

    issue_statuses = collect_unique_issue_statuses(projects)
    task_statuses_all = collect_unique_task_statuses(issues)

    issue_status_codes = StatusService.resolve_ids_to_codes(filters.issue_status) if filters.issue_status else None
    task_status_codes = TaskStatusService.resolve_ids_to_codes(filters.task_status) if filters.task_status else None
    tag_names = IssueTagService.resolve_ids_to_names(filters.tag) if filters.tag else None

    rows = WorkLogService.get_assignee_rows(
        filters.user or None, filters.project or None, filters.issue or None, tag_names,
        issue_status_codes, task_status_codes, filters.exclude_done_issue, filters.exclude_done_task,
        include_unassigned=include_unassigned
    )

    issue_ids = list({r['issue_id'] for r in rows})
    project_ids = list({r['project_id'] for r in rows})
    tags_map = TaskTagService.get_task_tags_map_bulk(issue_ids)
    status_labels_map = IssueService.get_status_labels_bulk(project_ids)
    task_status_labels_map = TaskStatusService.get_status_labels_bulk(issue_ids)

    return GridContext(
        users=users, projects=projects, issues=issues, all_tags=all_tags,
        issue_statuses=issue_statuses, task_statuses_all=task_statuses_all,
        rows=rows, tags_map=tags_map,
        status_labels_map=status_labels_map, task_status_labels_map=task_status_labels_map,
    )
