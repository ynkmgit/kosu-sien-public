"""アサイン集計サービス

責務: アサイン管理グリッドの事前集計計算のみ（純粋関数）
DB アクセスなし。WorkLogService.calculate_grid_totals() と同パターン。
"""
from typing import NamedTuple


def calc_weighted_progress(assignee_data: list[tuple]) -> int | None:
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


class GridAggregation(NamedTuple):
    """アサインメントグリッドの事前スキャン結果"""
    task_info: dict[int, dict]
    task_hierarchy: dict[int, tuple[int, int]]
    task_users: dict[int, list[int]]
    task_assignee_progress: dict[int, list[tuple]]
    project_estimate: dict[int, float]
    issue_estimate: dict[int, float]
    project_actual: dict[int, float]
    issue_actual: dict[int, float]
    task_actual_remaining: dict[int, float | None]
    project_actual_remaining: dict[int, float]
    issue_actual_remaining: dict[int, float]
    project_plan_total: dict[int, float]
    issue_plan_total: dict[int, float]
    task_plan_total: dict[int, float]
    task_hidden_plan: dict[int, float]
    task_unallocated: dict[int, float | None]
    project_unallocated: dict[int, float]
    issue_unallocated: dict[int, float]
    project_month_totals: dict[int, dict[str, float]]
    issue_month_totals: dict[int, dict[str, float]]
    task_month_totals: dict[int, dict[str, float]]


class AssignmentAggregationService:
    """アサイン管理グリッドの集計ロジック"""

    @staticmethod
    def prescan(rows: list[dict], plans: dict, plan_totals: dict) -> GridAggregation:
        """行データを事前スキャンし、全集計辞書を構築する（純粋関数）"""
        # タスクごとの担当者情報 + 階層マップ + ユーザーリスト
        task_info: dict[int, dict] = {}
        task_hierarchy: dict[int, tuple[int, int]] = {}
        task_users: dict[int, list[int]] = {}
        for row in rows:
            tid = row['task_id']
            if tid not in task_info:
                task_info[tid] = {'count': 0, 'first': None}
                task_hierarchy[tid] = (row['project_id'], row['issue_id'])
            if row.get('user_id') is not None:
                task_info[tid]['count'] += 1
                task_users.setdefault(tid, []).append(row['user_id'])
                if task_info[tid]['first'] is None:
                    task_info[tid]['first'] = {
                        'assignee_id': row.get('assignee_id'),
                        'user_id': row.get('user_id'),
                        'user_name': row.get('user_name'),
                    }

        # タスクごとの担当者進捗データ（加重平均用）
        task_assignee_progress: dict[int, list[tuple]] = {}
        for row in rows:
            tid = row['task_id']
            if row.get('user_id') is not None:
                uid = row['user_id']
                pr = row.get('progress_rate')
                pt = plan_totals.get((tid, uid), 0)
                task_assignee_progress.setdefault(tid, []).append((pr, pt))

        # 見積・実績工数集計 + 実際残（プロジェクト・案件・タスク別）
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
            progress = calc_weighted_progress(task_assignee_progress.get(tid, []))
            if est > 0 and progress is not None:
                ar = est * (1 - progress / 100)
                task_actual_remaining[tid] = ar
                project_actual_remaining[pid] = project_actual_remaining.get(pid, 0) + ar
                issue_actual_remaining[iid] = issue_actual_remaining.get(iid, 0) + ar
            else:
                task_actual_remaining[tid] = None

        # 山積計（全月合計、プロジェクト・案件・タスク別）
        project_plan_total: dict[int, float] = {}
        issue_plan_total: dict[int, float] = {}
        task_plan_total: dict[int, float] = {}
        for (t_id, u_id), total in plan_totals.items():
            if total <= 0:
                continue
            hierarchy = task_hierarchy.get(t_id)
            if hierarchy is None:
                continue
            p_id, i_id = hierarchy
            project_plan_total[p_id] = project_plan_total.get(p_id, 0) + total
            issue_plan_total[i_id] = issue_plan_total.get(i_id, 0) + total
            task_plan_total[t_id] = task_plan_total.get(t_id, 0) + total

        # タスク行のhidden_plan（マルチ担当で未割当ユーザーの計画値含む）
        task_hidden_plan: dict[int, float] = {}
        for tid_key, info in task_info.items():
            if info['count'] >= 2:
                assigned_sum = sum(
                    plan_totals.get((tid_key, uid), 0)
                    for uid in task_users.get(tid_key, [])
                )
                task_hidden_plan[tid_key] = task_plan_total.get(tid_key, 0) - assigned_sum

        # 未割当（実際残 − 山積計、実際残がないタスクは除外）
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

        # 月別計画工数集計（プロジェクト・案件・タスク別）
        project_month_totals: dict[int, dict[str, float]] = {}
        issue_month_totals: dict[int, dict[str, float]] = {}
        task_month_totals: dict[int, dict[str, float]] = {}
        for (t_id, u_id, ym), hours in plans.items():
            if hours <= 0:
                continue
            hierarchy = task_hierarchy.get(t_id)
            if hierarchy is None:
                continue
            p_id, i_id = hierarchy
            project_month_totals.setdefault(p_id, {})[ym] = project_month_totals.get(p_id, {}).get(ym, 0) + hours
            issue_month_totals.setdefault(i_id, {})[ym] = issue_month_totals.get(i_id, {}).get(ym, 0) + hours
            task_month_totals.setdefault(t_id, {})[ym] = task_month_totals.get(t_id, {}).get(ym, 0) + hours

        return GridAggregation(
            task_info=task_info, task_hierarchy=task_hierarchy, task_users=task_users,
            task_assignee_progress=task_assignee_progress,
            project_estimate=project_estimate, issue_estimate=issue_estimate,
            project_actual=project_actual, issue_actual=issue_actual,
            task_actual_remaining=task_actual_remaining,
            project_actual_remaining=project_actual_remaining, issue_actual_remaining=issue_actual_remaining,
            project_plan_total=project_plan_total, issue_plan_total=issue_plan_total, task_plan_total=task_plan_total,
            task_hidden_plan=task_hidden_plan,
            task_unallocated=task_unallocated, project_unallocated=project_unallocated, issue_unallocated=issue_unallocated,
            project_month_totals=project_month_totals, issue_month_totals=issue_month_totals, task_month_totals=task_month_totals,
        )
