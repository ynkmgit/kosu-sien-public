"""APIテスト用設定"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# テスト用一時DBを設定（importより前に）
_test_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db_path = _test_db_file.name
_test_db_file.close()
os.environ["DATABASE_PATH"] = _test_db_path

from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """テストDB初期化（セッション開始時）"""
    init_db()
    # テストデータ作成
    with get_db() as conn:
        # プロジェクト
        conn.execute("INSERT INTO project (cd, name, description) VALUES ('PJ001', 'プロジェクト1', '説明1')")
        conn.execute("INSERT INTO project (cd, name, description) VALUES ('PJ002', 'プロジェクト2', '説明2')")
        # ユーザー
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U001', '田中太郎', 'tanaka@example.com')")
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U002', '山田花子', 'yamada@example.com')")
    yield
    # クリーンアップ
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.fixture
def client():
    """FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def clean_db():
    """テストデータリセット（必要な場合に使用）"""
    with get_db() as conn:
        # 全テーブルクリア（依存関係順）
        conn.execute("DELETE FROM work_log")
        conn.execute("DELETE FROM task_assignee")
        conn.execute("DELETE FROM monthly_assignment")
        conn.execute("DELETE FROM issue_estimate_item")
        conn.execute("DELETE FROM task")
        conn.execute("DELETE FROM issue")
        conn.execute("DELETE FROM project_status")
        conn.execute("DELETE FROM user_attribute")
        conn.execute("DELETE FROM user")
        conn.execute("DELETE FROM project")
        # autoincrementリセット
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('user', 'project', 'issue', 'task')")
        # ベースデータ再作成（ID=1, 2になる）
        conn.executemany(
            "INSERT INTO project (cd, name, description) VALUES (?, ?, ?)",
            [("PJ001", "プロジェクト1", "説明1"), ("PJ002", "プロジェクト2", "説明2")],
        )
        # プロジェクトのデフォルトステータス
        default_statuses = [
            ("open", "未着手", 0),
            ("in_progress", "進行中", 1),
            ("done", "完了", 2),
        ]
        for project_id in [1, 2]:
            for code, name, order in default_statuses:
                conn.execute(
                    "INSERT INTO project_status (project_id, code, name, sort_order) VALUES (?, ?, ?, ?)",
                    (project_id, code, name, order)
                )
        conn.executemany(
            "INSERT INTO user (cd, name, email) VALUES (?, ?, ?)",
            [("U001", "田中太郎", "tanaka@example.com"), ("U002", "山田花子", "yamada@example.com")],
        )
    yield
