"""サービステスト用設定"""
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

from database import init_db, get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """テストDB初期化（セッション開始時）"""
    init_db()
    yield
    # クリーンアップ
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.fixture
def clean_db():
    """テストデータリセット"""
    with get_db() as conn:
        conn.execute("DELETE FROM work_log")
        conn.execute("DELETE FROM task_assignee")
        conn.execute("DELETE FROM issue_estimate_item")
        conn.execute("DELETE FROM task")
        conn.execute("DELETE FROM issue")
        conn.execute("DELETE FROM project_status")
        conn.execute("DELETE FROM project")
        conn.execute("DELETE FROM user_attribute")
        conn.execute("DELETE FROM user")
        conn.executemany(
            "INSERT INTO user (cd, name, email) VALUES (?, ?, ?)",
            [("U001", "田中太郎", "tanaka@example.com"), ("U002", "山田花子", "yamada@example.com")],
        )
    yield
