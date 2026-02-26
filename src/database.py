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
    ("open", "未着手", 0, 0),
    ("in_progress", "進行中", 1, 0),
    ("closed", "完了", 2, 1),
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
                is_done INTEGER DEFAULT 0,
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
            CREATE TABLE IF NOT EXISTS task_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                is_done INTEGER DEFAULT 0,
                FOREIGN KEY (issue_id) REFERENCES issue(id) ON DELETE CASCADE,
                UNIQUE(issue_id, code)
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
            CREATE TABLE IF NOT EXISTS task_monthly_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                year_month TEXT NOT NULL,
                planned_hours REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                UNIQUE(task_id, user_id, year_month)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS issue_tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT DEFAULT '#6b7280',
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (issue_id) REFERENCES issue(id) ON DELETE CASCADE,
                UNIQUE(issue_id, name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES issue_tag(id) ON DELETE CASCADE,
                UNIQUE(task_id, tag_id)
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_template (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL,
                options TEXT DEFAULT '{}',
                sort_order INTEGER DEFAULT 0
            )
        """)
        # インデックス（検索軸の高速化）
        _create_indexes(conn)
        # マイグレーション
        _migrate_cd(conn)
        _migrate_task_columns(conn)
        _migrate_user_columns(conn)
        # 既存プロジェクトにデフォルトステータスがない場合は作成
        _migrate_default_statuses(conn)
        # taskテーブルにstatusカラム追加 + 既存案件にデフォルト作業ステータス作成
        _migrate_task_status(conn)
        # ステータスにis_doneフラグ追加
        _migrate_status_is_done(conn)
        # task_assigneeにprogress_rateカラム追加
        _migrate_task_assignee_columns(conn)
        # デフォルト報告テンプレートのシード
        _seed_default_report_template(conn)


def _create_indexes(conn):
    """検索軸のインデックスを作成"""
    conn.execute("CREATE INDEX IF NOT EXISTS idx_issue_project_id ON issue(project_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_issue_id ON task(issue_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_work_log_task_id ON work_log(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_work_log_user_id ON work_log(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_work_log_work_date ON work_log(work_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_monthly_assignment_year_month ON monthly_assignment(year_month)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_monthly_plan_year_month ON task_monthly_plan(year_month)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_assignee_task_id ON task_assignee(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_assignee_user_id ON task_assignee(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_attribute_user_id ON user_attribute(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_issue_estimate_item_issue_id ON issue_estimate_item(issue_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_issue_tag_issue_id ON issue_tag(issue_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tag_task_id ON task_tag(task_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_tag_tag_id ON task_tag(tag_id)")


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
        "INSERT INTO project_status (project_id, code, name, sort_order, is_done) VALUES (?, ?, ?, ?, ?)",
        [(project_id, code, name, order, is_done) for code, name, order, is_done in DEFAULT_STATUSES]
    )


def _migrate_task_columns(conn):
    """taskテーブルに工数管理カラムを追加"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(task)").fetchall()]
    if "estimate_hours" not in cols:
        conn.execute("ALTER TABLE task ADD COLUMN estimate_hours REAL")
    if "progress_rate" not in cols:
        conn.execute("ALTER TABLE task ADD COLUMN progress_rate INTEGER")
    # client_estimate_hoursは廃止（顧客見積はissue_estimate_itemで管理）
    # 既存カラムは残すが新規追加はしない


def _migrate_user_columns(conn):
    """userテーブルのカラムマイグレーション"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(user)").fetchall()]
    if "is_active" not in cols:
        conn.execute("ALTER TABLE user ADD COLUMN is_active INTEGER DEFAULT 1")
        conn.execute("UPDATE user SET is_active = 1 WHERE is_active IS NULL")
    if "email" in cols:
        conn.execute("ALTER TABLE user DROP COLUMN email")


DEFAULT_TASK_STATUSES = [
    ("open", "未着手", 0, 0),
    ("in_progress", "進行中", 1, 0),
    ("done", "完了", 2, 1),
]


def _migrate_task_status(conn):
    """taskテーブルにstatusカラム追加 + 既存案件にデフォルト作業ステータス作成"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(task)").fetchall()]
    if "status" not in cols:
        conn.execute("ALTER TABLE task ADD COLUMN status TEXT DEFAULT 'open'")
    # 既存案件にデフォルト作業ステータスがなければ作成
    issues = conn.execute("SELECT id FROM issue").fetchall()
    for issue in issues:
        issue_id = issue[0]
        count = conn.execute(
            "SELECT COUNT(*) FROM task_status WHERE issue_id = ?",
            (issue_id,)
        ).fetchone()[0]
        if count == 0:
            create_default_task_statuses(conn, issue_id)


def create_default_task_statuses(conn, issue_id: int):
    """案件にデフォルト作業ステータスを作成"""
    conn.executemany(
        "INSERT INTO task_status (issue_id, code, name, sort_order, is_done) VALUES (?, ?, ?, ?, ?)",
        [(issue_id, code, name, order, is_done) for code, name, order, is_done in DEFAULT_TASK_STATUSES]
    )


def _migrate_status_is_done(conn):
    """project_status/task_statusにis_doneカラムを追加"""
    for table in ("project_status", "task_status"):
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "is_done" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN is_done INTEGER DEFAULT 0")


def _migrate_task_assignee_columns(conn):
    """task_assigneeテーブルにカラム追加"""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(task_assignee)").fetchall()}
    if 'progress_rate' not in cols:
        conn.execute("ALTER TABLE task_assignee ADD COLUMN progress_rate INTEGER")


# デフォルト報告テンプレート
DEFAULT_REPORT_TEMPLATE = """業務終了します。
【工数実績】
 {total_hours}H
【作業実績、進捗率】
@project
@issue
@task   {project_name} {issue_name} {task_name} ({progress}%)"""


def _seed_default_report_template(conn):
    """report_templateテーブルが空なら初期テンプレートを挿入"""
    count = conn.execute("SELECT COUNT(*) FROM report_template").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO report_template (name, body, options, sort_order) VALUES (?, ?, ?, ?)",
            ("業務終了報告", DEFAULT_REPORT_TEMPLATE, '{"hideZeroProgress": false}', 0)
        )
