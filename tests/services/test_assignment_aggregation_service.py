"""AssignmentAggregationService のテスト（純粋関数、DB不要）"""
from services.assignment_aggregation_service import AssignmentAggregationService


def _make_row(task_id, project_id, issue_id, user_id=None, assignee_id=None,
              user_name=None, estimate_hours=0, actual_hours=0, progress_rate=None, **extra):
    row = {
        'task_id': task_id, 'project_id': project_id, 'issue_id': issue_id,
        'user_id': user_id, 'assignee_id': assignee_id, 'user_name': user_name,
        'estimate_hours': estimate_hours, 'actual_hours': actual_hours,
        'progress_rate': progress_rate,
        'project_name': f'P{project_id}', 'project_cd': f'P{project_id:03d}',
        'issue_cd': f'I{issue_id:03d}', 'issue_name': f'Issue{issue_id}',
        'task_name': f'Task{task_id}', 'user_cd': f'U{user_id:03d}' if user_id else None,
    }
    row.update(extra)
    return row


class TestPrescanBasic:
    def test_empty_rows(self):
        """空リストでもエラーなし"""
        agg = AssignmentAggregationService.prescan([], {}, {})
        assert agg.task_info == {}
        assert agg.project_estimate == {}

    def test_single_task_single_assignee(self):
        """1タスク1担当者の基本集計"""
        rows = [_make_row(1, 10, 100, user_id=1, assignee_id=1,
                          user_name='Alice', estimate_hours=10, actual_hours=3, progress_rate=30)]
        plans = {(1, 1, '2026-03'): 5.0}
        plan_totals = {(1, 1): 5.0}

        agg = AssignmentAggregationService.prescan(rows, plans, plan_totals)

        assert agg.task_info[1]['count'] == 1
        assert agg.task_info[1]['first']['user_name'] == 'Alice'
        assert agg.project_estimate[10] == 10
        assert agg.issue_estimate[100] == 10
        assert agg.project_actual[10] == 3
        assert agg.task_plan_total[1] == 5.0
        assert agg.task_month_totals[1] == {'2026-03': 5.0}

    def test_multi_task_aggregation(self):
        """複数タスクのプロジェクト・案件集計"""
        rows = [
            _make_row(1, 10, 100, user_id=1, estimate_hours=10, actual_hours=2),
            _make_row(2, 10, 100, user_id=2, estimate_hours=20, actual_hours=5),
        ]
        agg = AssignmentAggregationService.prescan(rows, {}, {})

        assert agg.project_estimate[10] == 30
        assert agg.issue_estimate[100] == 30
        assert agg.project_actual[10] == 7

    def test_unassigned_task(self):
        """担当者なしのタスク"""
        rows = [_make_row(1, 10, 100, user_id=None, estimate_hours=5)]
        agg = AssignmentAggregationService.prescan(rows, {}, {})

        assert agg.task_info[1]['count'] == 0
        assert agg.task_info[1]['first'] is None

    def test_multi_assignee_hidden_plan(self):
        """2名以上の担当者がいる場合のhidden_plan計算"""
        rows = [
            _make_row(1, 10, 100, user_id=1, assignee_id=1, user_name='A', estimate_hours=10),
            _make_row(1, 10, 100, user_id=2, assignee_id=2, user_name='B', estimate_hours=10),
        ]
        # 外部ユーザー(uid=99)にも山積がある場合
        plan_totals = {(1, 1): 5.0, (1, 2): 3.0, (1, 99): 2.0}
        agg = AssignmentAggregationService.prescan(rows, {}, plan_totals)

        assert agg.task_info[1]['count'] == 2
        # hidden_plan = task_plan_total(10) - assigned_sum(5+3) = 2
        assert agg.task_hidden_plan[1] == 2.0

    def test_actual_remaining_with_progress(self):
        """見積と進捗率から実際残を計算"""
        rows = [_make_row(1, 10, 100, user_id=1, estimate_hours=100, actual_hours=30, progress_rate=50)]
        plan_totals = {(1, 1): 10.0}
        agg = AssignmentAggregationService.prescan(rows, {}, plan_totals)

        # 実際残 = 見積 * (1 - 進捗率/100) = 100 * 0.5 = 50
        assert agg.task_actual_remaining[1] == 50.0
        assert agg.project_actual_remaining[10] == 50.0

    def test_actual_remaining_none_when_no_estimate(self):
        """見積0の場合は実際残=None"""
        rows = [_make_row(1, 10, 100, user_id=1, estimate_hours=0, progress_rate=50)]
        agg = AssignmentAggregationService.prescan(rows, {}, {})

        assert agg.task_actual_remaining[1] is None

    def test_unallocated_calculation(self):
        """未割当 = 実際残 - 山積計"""
        rows = [_make_row(1, 10, 100, user_id=1, estimate_hours=100, actual_hours=0, progress_rate=50)]
        plan_totals = {(1, 1): 30.0}
        agg = AssignmentAggregationService.prescan(rows, {}, plan_totals)

        # 実際残 = 100 * 0.5 = 50, 未割当 = 50 - 30 = 20
        assert agg.task_unallocated[1] == 20.0
        assert agg.project_unallocated[10] == 20.0
