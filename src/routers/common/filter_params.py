"""フィルターパラメータ共通定義

責務: URLフィルターパラメータの受け取りと構造化のみ
"""
from dataclasses import dataclass
from fastapi import Query


@dataclass
class FilterParams:
    """全画面共通のフィルターパラメータ"""
    user: list[int]
    project: list[int]
    issue: list[int]
    tag: list[int]
    issue_status: list[int]
    task_status: list[int]
    exclude_done_issue: bool
    exclude_done_task: bool
    fold: str

    def to_dict(self) -> dict:
        """テンプレート用の辞書形式に変換"""
        return {
            "user": self.user,
            "project": self.project,
            "issue": self.issue,
            "tag": self.tag,
            "issue_status": self.issue_status,
            "task_status": self.task_status,
            "exclude_done_issue": self.exclude_done_issue,
            "exclude_done_task": self.exclude_done_task,
            "fold": self.fold,
        }

    def has_filters(self) -> bool:
        """フィルターが設定されているか"""
        return bool(self.user or self.project or self.issue or self.tag or self.issue_status or self.task_status or self.exclude_done_issue or self.exclude_done_task)


def get_filter_params(
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[]),
    tag: list[int] = Query(default=[]),
    issue_status: list[int] = Query(default=[]),
    task_status: list[int] = Query(default=[]),
    exclude_done_issue: bool = Query(default=False),
    exclude_done_task: bool = Query(default=False),
    fold: str = Query(default=""),
) -> FilterParams:
    """フィルターパラメータを取得（FastAPI依存性）"""
    return FilterParams(user=user, project=project, issue=issue, tag=tag,
                        issue_status=issue_status, task_status=task_status,
                        exclude_done_issue=exclude_done_issue, exclude_done_task=exclude_done_task, fold=fold)
