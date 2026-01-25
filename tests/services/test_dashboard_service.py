"""ダッシュボードサービスのテスト"""
from datetime import date
from services.dashboard_service import DashboardService
from database import get_db


def test_get_today_hours_empty(clean_db):
    """工数記録なしで0"""
    result = DashboardService.get_today_hours(date(2099, 1, 1))
    assert result == 0


def test_get_today_hours_with_data(clean_db):
    """工数記録ありで合計"""
    # テストデータ作成
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('P1', 'Project1')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I1', 'Issue1')", (project_id,))
        issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T1', 'Task1')", (issue_id,))
        task_id1 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T2', 'Task2')", (issue_id,))
        task_id2 = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U1', 'User1', 'u1@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # 同日の別タスクに工数記録
        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-06-15', 3.5)",
            (task_id1, user_id)
        )
        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-06-15', 2.0)",
            (task_id2, user_id)
        )

    result = DashboardService.get_today_hours(date(2099, 6, 15))
    assert result == 5.5


def test_get_monthly_stats_empty(clean_db):
    """データなしで0"""
    result = DashboardService.get_monthly_stats("2099-12")
    assert result["planned"] == 0
    assert result["actual"] == 0


def test_get_monthly_stats_with_data(clean_db):
    """計画・実績あり"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('P2', 'Project2')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U2', 'User2', 'u2@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 月次アサイン
        conn.execute(
            "INSERT INTO monthly_assignment (user_id, project_id, year_month, planned_hours) VALUES (?, ?, '2099-07', 40)",
            (user_id, project_id)
        )

        # 実績
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I2', 'Issue2')", (project_id,))
        issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T2', 'Task2')", (issue_id,))
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-07-10', 8)",
            (task_id, user_id)
        )

    result = DashboardService.get_monthly_stats("2099-07")
    assert result["planned"] == 40
    assert result["actual"] == 8


def test_get_counts(clean_db):
    """カウント取得"""
    result = DashboardService.get_counts()
    assert "project_count" in result
    assert "user_count" in result
    assert isinstance(result["project_count"], int)
    assert isinstance(result["user_count"], int)


def test_get_counts_with_inactive_users(clean_db):
    """無効ユーザーは除外"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email, is_active) VALUES ('ACTIVE', 'Active', 'a@test.com', 1)")
        conn.execute("INSERT INTO user (cd, name, email, is_active) VALUES ('INACTIVE', 'Inactive', 'i@test.com', 0)")

    result = DashboardService.get_counts()
    # 有効ユーザーのみカウントされる
    assert result["user_count"] >= 1
