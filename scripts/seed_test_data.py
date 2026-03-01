#!/usr/bin/env python3
"""テストデータ投入スクリプト

sample/test_data_draft.json からユーザー・プロジェクト・案件を
DBに直接投入する。既存データは全クリアされる。
"""
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import get_db, create_default_statuses, create_default_task_statuses

STATUS_MAP = {
    "open": "open",
    "in_progress": "in_progress",
    "closed": "closed",
}


def clear_all(conn):
    """全テーブルのデータをクリア（スキーマは維持）"""
    tables = [
        "work_log", "task_monthly_plan", "monthly_assignment",
        "task_tag", "task_assignee", "issue_tag",
        "issue_estimate_item", "task_status", "task",
        "project_status", "issue", "user_setting",
        "user_attribute", "user_attribute_option", "user_attribute_type",
        "report_template", "user", "project",
    ]
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
    # AUTO INCREMENTリセット
    conn.execute("DELETE FROM sqlite_sequence")
    print(f"  全{len(tables)}テーブルをクリア")


def seed_users(conn, users):
    """ユーザー投入"""
    for u in users:
        conn.execute(
            "INSERT INTO user (cd, name, is_active) VALUES (?, ?, 1)",
            (u["cd"], u["name"])
        )
    print(f"  ユーザー: {len(users)}名")


def seed_projects(conn, projects):
    """プロジェクト投入"""
    pj_id_map = {}
    for p in projects:
        cursor = conn.execute(
            "INSERT INTO project (cd, name, description) VALUES (?, ?, ?)",
            (p["cd"], p["name"], p.get("description", ""))
        )
        pj_id_map[p["cd"]] = cursor.lastrowid
        create_default_statuses(conn, cursor.lastrowid)
    print(f"  プロジェクト: {len(projects)}件")
    return pj_id_map


def seed_issues(conn, pj_cd, pj_id, issues):
    """案件投入"""
    for iss in issues:
        status = STATUS_MAP.get(iss.get("status", "open"), "open")
        cursor = conn.execute(
            "INSERT INTO issue (cd, project_id, name, description, status) VALUES (?, ?, ?, ?, ?)",
            (iss["cd"], pj_id, iss["name"], iss.get("description", ""), status)
        )
        issue_id = cursor.lastrowid
        create_default_task_statuses(conn, issue_id)

        # 工数があればissue_estimate_itemに登録
        hours = iss.get("hours")
        if hours and float(hours) > 0:
            conn.execute(
                "INSERT INTO issue_estimate_item (issue_id, name, hours, sort_order) VALUES (?, ?, ?, 0)",
                (issue_id, "見積工数", float(hours))
            )
    print(f"  案件 [{pj_cd}]: {len(issues)}件")


def seed_report_template(conn):
    """デフォルト報告テンプレート"""
    template = """業務終了します。
【工数実績】
 {total_hours}H
【作業実績、進捗率】
@project
@issue
@task   {project_name} {issue_name} {task_name} ({progress}%)"""
    conn.execute(
        "INSERT INTO report_template (name, body, options, sort_order) VALUES (?, ?, ?, ?)",
        ("業務終了報告", template, '{"hideZeroProgress": false}', 0)
    )
    print("  報告テンプレート: 1件")


def main():
    draft_path = PROJECT_ROOT / "sample" / "test_data_draft.json"
    if not draft_path.exists():
        print(f"エラー: {draft_path} が見つかりません")
        sys.exit(1)

    with open(draft_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 60)
    print("テストデータ投入")
    print("=" * 60)

    with get_db() as conn:
        # 1. クリア
        print("\n[1/4] データクリア")
        clear_all(conn)

        # 2. ユーザー
        print("\n[2/4] ユーザー投入")
        seed_users(conn, data["users"])

        # 3. プロジェクト
        print("\n[3/4] プロジェクト投入")
        pj_id_map = seed_projects(conn, data["projects"])

        # 4. 案件
        print("\n[4/4] 案件投入")
        for pj_cd, issues in data["issues"].items():
            pj_id = pj_id_map[pj_cd]
            seed_issues(conn, pj_cd, pj_id, issues)

        # 報告テンプレート
        seed_report_template(conn)

    # 検証
    print("\n" + "=" * 60)
    print("検証")
    print("=" * 60)
    with get_db() as conn:
        u_count = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        p_count = conn.execute("SELECT COUNT(*) FROM project").fetchone()[0]
        i_count = conn.execute("SELECT COUNT(*) FROM issue").fetchone()[0]
        ps_count = conn.execute("SELECT COUNT(*) FROM project_status").fetchone()[0]
        ts_count = conn.execute("SELECT COUNT(*) FROM task_status").fetchone()[0]
        ei_count = conn.execute("SELECT COUNT(*) FROM issue_estimate_item").fetchone()[0]
        print(f"  user:             {u_count}")
        print(f"  project:          {p_count}")
        print(f"  issue:            {i_count}")
        print(f"  project_status:   {ps_count}")
        print(f"  task_status:      {ts_count}")
        print(f"  issue_estimate:   {ei_count}")

    print("\n完了!")


if __name__ == "__main__":
    main()
