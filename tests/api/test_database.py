"""データベーススキーマテスト"""
import pytest


class TestSchemaExists:
    """テーブル存在確認"""

    def test_monthly_assignment_table_exists(self, client):
        """monthly_assignmentテーブルが存在する"""
        from database import get_db
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_assignment'"
            ).fetchall()
        assert len(tables) == 1

    def test_issue_estimate_item_table_exists(self, client):
        """issue_estimate_itemテーブルが存在する"""
        from database import get_db
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='issue_estimate_item'"
            ).fetchall()
        assert len(tables) == 1

    def test_task_assignee_table_exists(self, client):
        """task_assigneeテーブルが存在する"""
        from database import get_db
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='task_assignee'"
            ).fetchall()
        assert len(tables) == 1

    def test_work_log_table_exists(self, client):
        """work_logテーブルが存在する"""
        from database import get_db
        with get_db() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='work_log'"
            ).fetchall()
        assert len(tables) == 1


class TestTaskColumns:
    """taskテーブルのカラム確認"""

    def test_task_has_estimate_hours(self, client):
        """taskテーブルにestimate_hoursカラムがある"""
        from database import get_db
        with get_db() as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(task)").fetchall()]
        assert "estimate_hours" in cols

    def test_task_has_progress_rate(self, client):
        """taskテーブルにprogress_rateカラムがある"""
        from database import get_db
        with get_db() as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(task)").fetchall()]
        assert "progress_rate" in cols


class TestUserColumns:
    """userテーブルのカラム確認"""

    def test_user_has_is_active(self, client):
        """userテーブルにis_activeカラムがある"""
        from database import get_db
        with get_db() as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(user)").fetchall()]
        assert "is_active" in cols

    def test_user_is_active_default_is_1(self, client):
        """既存ユーザーのis_activeはデフォルト1"""
        from database import get_db
        with get_db() as conn:
            users = conn.execute("SELECT is_active FROM user").fetchall()
        for user in users:
            assert user[0] == 1


class TestUniqueConstraints:
    """一意制約の確認"""

    def test_monthly_assignment_unique(self, client):
        """monthly_assignmentの一意制約が機能する"""
        from database import get_db
        import sqlite3
        with get_db() as conn:
            # 最初の挿入は成功
            conn.execute(
                "INSERT INTO monthly_assignment (user_id, project_id, year_month, planned_hours) VALUES (1, 1, '2026-01', 40.0)"
            )
            # 同じ組み合わせは失敗
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO monthly_assignment (user_id, project_id, year_month, planned_hours) VALUES (1, 1, '2026-01', 80.0)"
                )

    def test_issue_estimate_item_unique(self, client):
        """issue_estimate_itemの一意制約が機能する"""
        from database import get_db
        import sqlite3
        with get_db() as conn:
            # 案件を作成
            conn.execute("INSERT INTO issue (cd, project_id, name, status) VALUES ('TEST', 1, 'テスト案件', 'open')")
            issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # 最初の挿入は成功
            conn.execute(
                "INSERT INTO issue_estimate_item (issue_id, name, hours) VALUES (?, '設計', 16.0)",
                (issue_id,)
            )
            # 同じ組み合わせは失敗
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO issue_estimate_item (issue_id, name, hours) VALUES (?, '設計', 24.0)",
                    (issue_id,)
                )

    def test_task_assignee_unique(self, client):
        """task_assigneeの一意制約が機能する"""
        from database import get_db
        import sqlite3
        with get_db() as conn:
            # 案件と作業を作成
            conn.execute("INSERT INTO issue (cd, project_id, name, status) VALUES ('TA-TEST', 1, 'テスト案件', 'open')")
            issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO task (cd, issue_id, name) VALUES ('T001', ?, 'テスト作業')", (issue_id,))
            task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # 最初の挿入は成功
            conn.execute("INSERT INTO task_assignee (task_id, user_id) VALUES (?, 1)", (task_id,))
            # 同じ組み合わせは失敗
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO task_assignee (task_id, user_id) VALUES (?, 1)", (task_id,))

    def test_work_log_unique(self, client):
        """work_logの一意制約が機能する"""
        from database import get_db
        import sqlite3
        with get_db() as conn:
            # 案件と作業を作成
            conn.execute("INSERT INTO issue (cd, project_id, name, status) VALUES ('WL-TEST', 1, 'テスト案件', 'open')")
            issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO task (cd, issue_id, name) VALUES ('T001', ?, 'テスト作業')", (issue_id,))
            task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # 最初の挿入は成功
            conn.execute(
                "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, 1, '2026-01-18', 2.0)",
                (task_id,)
            )
            # 同じ組み合わせは失敗
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, 1, '2026-01-18', 4.0)",
                    (task_id,)
                )


class TestCascadeDelete:
    """CASCADE削除の確認"""

    def test_issue_delete_cascades_estimate_items(self, client):
        """案件削除時に見積内訳も削除される"""
        from database import get_db
        with get_db() as conn:
            # 案件と見積内訳を作成
            conn.execute("INSERT INTO issue (cd, project_id, name, status) VALUES ('CASCADE-1', 1, 'テスト案件', 'open')")
            issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO issue_estimate_item (issue_id, name, hours) VALUES (?, '設計', 16.0)", (issue_id,))
            conn.execute("INSERT INTO issue_estimate_item (issue_id, name, hours) VALUES (?, '実装', 24.0)", (issue_id,))

            # 見積内訳が存在することを確認
            count = conn.execute("SELECT COUNT(*) FROM issue_estimate_item WHERE issue_id = ?", (issue_id,)).fetchone()[0]
            assert count == 2

            # 案件を削除
            conn.execute("DELETE FROM issue WHERE id = ?", (issue_id,))

            # 見積内訳も削除されていることを確認
            count = conn.execute("SELECT COUNT(*) FROM issue_estimate_item WHERE issue_id = ?", (issue_id,)).fetchone()[0]
            assert count == 0

    def test_task_delete_cascades_work_log(self, client):
        """作業削除時に工数記録も削除される"""
        from database import get_db
        with get_db() as conn:
            # 案件、作業、工数記録を作成
            conn.execute("INSERT INTO issue (cd, project_id, name, status) VALUES ('CASCADE-2', 1, 'テスト案件', 'open')")
            issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO task (cd, issue_id, name) VALUES ('T001', ?, 'テスト作業')", (issue_id,))
            task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, 1, '2026-01-18', 2.0)", (task_id,))

            # 工数記録が存在することを確認
            count = conn.execute("SELECT COUNT(*) FROM work_log WHERE task_id = ?", (task_id,)).fetchone()[0]
            assert count == 1

            # 作業を削除
            conn.execute("DELETE FROM task WHERE id = ?", (task_id,))

            # 工数記録も削除されていることを確認
            count = conn.execute("SELECT COUNT(*) FROM work_log WHERE task_id = ?", (task_id,)).fetchone()[0]
            assert count == 0
