"""データベース接続管理"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# プロジェクトルートを基準にDBパスを解決（実行ディレクトリに依存しない）
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = Path(os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "app.db"))

# デフォルトステータス定義
DEFAULT_STATUSES = [
    ("open", "未着手", 0),
    ("in_progress", "進行中", 1),
    ("closed", "完了", 2),
]


@contextmanager
def get_db():
    """DBコネクションのコンテキストマネージャー"""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # 外部キー制約を有効化
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """テーブル作成とサンプルデータ挿入"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cd TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cd TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS issue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cd TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
                UNIQUE(project_id, cd)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS project_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
                UNIQUE(project_id, code)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_attribute_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_attribute_option (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (type_id) REFERENCES user_attribute_type(id) ON DELETE CASCADE,
                UNIQUE(type_id, code)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_attribute (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (type_id) REFERENCES user_attribute_type(id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES user_attribute_option(id) ON DELETE CASCADE,
                UNIQUE(user_id, type_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cd TEXT NOT NULL,
                issue_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                estimate_hours REAL,
                progress_rate INTEGER,
                FOREIGN KEY (issue_id) REFERENCES issue(id) ON DELETE CASCADE,
                UNIQUE(issue_id, cd)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS monthly_assignment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                year_month TEXT NOT NULL,
                planned_hours REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES project(id) ON DELETE CASCADE,
                UNIQUE(user_id, project_id, year_month)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS issue_estimate_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                hours REAL NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (issue_id) REFERENCES issue(id) ON DELETE CASCADE,
                UNIQUE(issue_id, name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_assignee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                UNIQUE(task_id, user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                work_date DATE NOT NULL,
                hours REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                UNIQUE(task_id, user_id, work_date)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_setting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                UNIQUE(user_id, setting_key)
            )
        """)
        # マイグレーション
        _migrate_cd(conn)
        _migrate_task_columns(conn)
        _migrate_user_columns(conn)
        # 既存プロジェクトにデフォルトステータスがない場合は作成
        _migrate_default_statuses(conn)


def _migrate_cd(conn):
    """既存テーブルにcdカラムがない場合に追加"""
    # projectテーブル
    cols = [row[1] for row in conn.execute("PRAGMA table_info(project)").fetchall()]
    if "cd" not in cols:
        conn.execute("ALTER TABLE project ADD COLUMN cd TEXT")
        for row in conn.execute("SELECT id FROM project").fetchall():
            conn.execute("UPDATE project SET cd = ? WHERE id = ?", (f"PJ{row[0]:03d}", row[0]))
        # UNIQUE制約は後から追加できないため、既存データのみ更新

    # userテーブル
    cols = [row[1] for row in conn.execute("PRAGMA table_info(user)").fetchall()]
    if "cd" not in cols:
        conn.execute("ALTER TABLE user ADD COLUMN cd TEXT")
        for row in conn.execute("SELECT id FROM user").fetchall():
            conn.execute("UPDATE user SET cd = ? WHERE id = ?", (f"U{row[0]:03d}", row[0]))


def _migrate_default_statuses(conn):
    """既存プロジェクトにデフォルトステータスがない場合に作成"""
    projects = conn.execute("SELECT id FROM project").fetchall()
    for project in projects:
        project_id = project[0]
        # ステータスが1件もなければデフォルト作成
        count = conn.execute(
            "SELECT COUNT(*) FROM project_status WHERE project_id = ?",
            (project_id,)
        ).fetchone()[0]
        if count == 0:
            create_default_statuses(conn, project_id)


def create_default_statuses(conn, project_id: int):
    """プロジェクトにデフォルトステータスを作成"""
    conn.executemany(
        "INSERT INTO project_status (project_id, code, name, sort_order) VALUES (?, ?, ?, ?)",
        [(project_id, code, name, order) for code, name, order in DEFAULT_STATUSES]
    )


def _migrate_task_columns(conn):
    """taskテーブルに工数管理カラムを追加"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(task)").fetchall()]
    if "estimate_hours" not in cols:
        conn.execute("ALTER TABLE task ADD COLUMN estimate_hours REAL")
    if "progress_rate" not in cols:
        conn.execute("ALTER TABLE task ADD COLUMN progress_rate INTEGER")


def _migrate_user_columns(conn):
    """userテーブルにis_activeカラムを追加"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(user)").fetchall()]
    if "is_active" not in cols:
        conn.execute("ALTER TABLE user ADD COLUMN is_active INTEGER DEFAULT 1")
        # 既存ユーザーは有効に設定
        conn.execute("UPDATE user SET is_active = 1 WHERE is_active IS NULL")
