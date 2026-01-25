"""10人規模チームのテストデータ生成スクリプト"""
import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "app.db"

def get_working_days(year: int, month: int, until_day: int = None) -> list[date]:
    """指定月の営業日（平日）を取得"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    if until_day:
        last_day = min(last_day, until_day)

    days = []
    for d in range(1, last_day + 1):
        dt = date(year, month, d)
        if dt.weekday() < 5:  # 月〜金
            days.append(dt)
    return days


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # 既存データ取得
        users = conn.execute(
            "SELECT id, cd, name FROM user WHERE is_active = 1 OR is_active IS NULL ORDER BY cd"
        ).fetchall()
        print(f"有効ユーザー: {len(users)}人")

        projects = conn.execute("SELECT id, cd, name FROM project ORDER BY cd").fetchall()
        print(f"プロジェクト: {len(projects)}件")

        # PJ001 (ASPIT) の案件と作業を取得
        issues = conn.execute("""
            SELECT i.id, i.cd, i.name, p.id as project_id
            FROM issue i
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ001'
            ORDER BY i.cd
        """).fetchall()
        print(f"PJ001案件: {len(issues)}件")

        tasks = conn.execute("""
            SELECT t.id, t.cd, t.name, i.id as issue_id, i.cd as issue_cd
            FROM task t
            JOIN issue i ON t.issue_id = i.id
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ001'
            ORDER BY i.cd, t.cd
        """).fetchall()
        print(f"PJ001作業: {len(tasks)}件")

        # === 月次アサイン設定 ===
        print("\n=== 月次アサイン設定 ===")

        # 12月と1月のアサイン（10人分）
        # user_id -> {project_cd: hours}
        assignment_plan = {
            1: {"PJ001": 120, "PJ002": 40},   # U001 PM: 主にASPIT
            2: {"PJ001": 140, "PJ002": 20},   # U002 リーダー: ASPIT中心
            3: {"PJ001": 160},                 # U003: ASPIT専任
            4: {"PJ001": 120, "PJ003": 40},   # U004: ASPIT+保守
            5: {"PJ001": 160},                 # U005 BP: ASPIT専任
            6: {"PJ001": 140, "PJ002": 20},   # U006 BP: ASPIT中心
            7: {"PJ001": 160},                 # U007 派遣: ASPIT専任
            8: {"PJ001": 40, "PJ003": 40},    # U008 待機: 少ない稼働
            9: {"PJ001": 120},                 # U009: 12月まで
            10: {"PJ001": 140, "PJ002": 20},  # U010 リーダー: ASPIT中心
        }

        project_id_map = {p["cd"]: p["id"] for p in projects}

        for year_month in ["2025-12", "2026-01"]:
            for user in users:
                user_id = user["id"]
                if user_id not in assignment_plan:
                    continue

                # U009は12月まで
                if user_id == 9 and year_month == "2026-01":
                    continue

                for project_cd, hours in assignment_plan[user_id].items():
                    if project_cd not in project_id_map:
                        continue
                    project_id = project_id_map[project_cd]

                    # 既存チェック
                    existing = conn.execute(
                        "SELECT id FROM monthly_assignment WHERE user_id=? AND project_id=? AND year_month=?",
                        (user_id, project_id, year_month)
                    ).fetchone()

                    if existing:
                        conn.execute(
                            "UPDATE monthly_assignment SET planned_hours=? WHERE id=?",
                            (hours, existing["id"])
                        )
                    else:
                        conn.execute(
                            "INSERT INTO monthly_assignment (user_id, project_id, year_month, planned_hours) VALUES (?,?,?,?)",
                            (user_id, project_id, year_month, hours)
                        )
            print(f"  {year_month}: アサイン設定完了")

        # === 担当割当（task_assignee）の設定 ===
        print("\n=== 担当割当設定 ===")

        # 各作業に担当者を割り当て
        # task_id -> [user_ids]
        task_assignees = {}

        for task in tasks:
            task_id = task["id"]
            issue_cd = task["issue_cd"]
            task_cd = task["cd"]

            # 案件と作業に応じて担当を割り当て
            if issue_cd == "0000":  # 全体管理
                task_assignees[task_id] = [1, 2, 10]  # PM, リーダー
            elif issue_cd == "V2A9-0001":  # 基盤構築
                if task_cd == "T001":  # 設計
                    task_assignees[task_id] = [1, 2]  # PM, リーダー
                elif task_cd == "T002":  # 実装
                    task_assignees[task_id] = [2, 3, 4, 5]  # 開発メンバー
                elif task_cd == "T003":  # テスト
                    task_assignees[task_id] = [7, 8]  # テスト担当
            elif issue_cd == "V2A9-0002":  # 画面開発
                task_assignees[task_id] = [3, 4, 5, 6]  # 開発メンバー
            elif issue_cd == "V2A9-0003":  # API開発
                task_assignees[task_id] = [5, 6, 9, 10]  # 開発メンバー

        # 全案件に作業がない場合は追加
        for issue in issues:
            issue_id = issue["id"]
            issue_cd = issue["cd"]

            # この案件の作業を確認
            existing_tasks = conn.execute(
                "SELECT id FROM task WHERE issue_id = ?", (issue_id,)
            ).fetchall()

            if not existing_tasks:
                # 作業を追加
                if issue_cd == "0000":
                    new_tasks = [("T001", "PMO"), ("T002", "進捗管理"), ("T003", "課題管理")]
                elif issue_cd == "V2A9-0002":
                    new_tasks = [("T001", "設計"), ("T002", "実装"), ("T003", "テスト")]
                elif issue_cd == "V2A9-0003":
                    new_tasks = [("T001", "設計"), ("T002", "実装"), ("T003", "テスト")]
                else:
                    new_tasks = []

                for cd, name in new_tasks:
                    conn.execute(
                        "INSERT INTO task (issue_id, cd, name) VALUES (?,?,?)",
                        (issue_id, cd, name)
                    )
                    task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                    # 担当割当
                    if issue_cd == "0000":
                        task_assignees[task_id] = [1, 2, 10]
                    elif issue_cd == "V2A9-0002":
                        task_assignees[task_id] = [3, 4, 5, 6]
                    elif issue_cd == "V2A9-0003":
                        task_assignees[task_id] = [5, 6, 9, 10]

                print(f"  {issue_cd}: 作業追加 {len(new_tasks)}件")

        # 担当割当を登録
        for task_id, user_ids in task_assignees.items():
            for user_id in user_ids:
                existing = conn.execute(
                    "SELECT id FROM task_assignee WHERE task_id=? AND user_id=?",
                    (task_id, user_id)
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO task_assignee (task_id, user_id) VALUES (?,?)",
                        (task_id, user_id)
                    )
        print(f"  担当割当: {sum(len(u) for u in task_assignees.values())}件")

        # === 見積内訳設定 ===
        print("\n=== 見積内訳設定 ===")

        estimate_plan = {
            "0000": [("PMO", 40), ("進捗管理", 20), ("課題管理", 20)],
            "V2A9-0001": [],  # 既存
            "V2A9-0002": [("設計", 40), ("実装", 80), ("テスト", 40)],
            "V2A9-0003": [("設計", 32), ("実装", 64), ("テスト", 24)],
        }

        for issue in issues:
            issue_id = issue["id"]
            issue_cd = issue["cd"]

            if issue_cd not in estimate_plan or not estimate_plan[issue_cd]:
                continue

            for name, hours in estimate_plan[issue_cd]:
                existing = conn.execute(
                    "SELECT id FROM issue_estimate_item WHERE issue_id=? AND name=?",
                    (issue_id, name)
                ).fetchone()
                if not existing:
                    conn.execute(
                        "INSERT INTO issue_estimate_item (issue_id, name, hours) VALUES (?,?,?)",
                        (issue_id, name, hours)
                    )
            print(f"  {issue_cd}: 見積設定完了")

        # === 実績データ生成 ===
        print("\n=== 実績データ生成 ===")

        # 再取得（新規追加分含む）
        all_tasks = conn.execute("""
            SELECT t.id, t.cd, t.name, i.id as issue_id, i.cd as issue_cd, p.id as project_id
            FROM task t
            JOIN issue i ON t.issue_id = i.id
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ001'
            ORDER BY i.cd, t.cd
        """).fetchall()

        all_assignees = conn.execute("""
            SELECT ta.task_id, ta.user_id
            FROM task_assignee ta
            JOIN task t ON ta.task_id = t.id
            JOIN issue i ON t.issue_id = i.id
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ001'
        """).fetchall()

        # task_id -> [user_ids]
        task_user_map = {}
        for a in all_assignees:
            tid = a["task_id"]
            if tid not in task_user_map:
                task_user_map[tid] = []
            task_user_map[tid].append(a["user_id"])

        # 12月の営業日
        dec_days = get_working_days(2025, 12)
        print(f"  12月営業日: {len(dec_days)}日")

        # 1月1-18日の営業日
        jan_days = get_working_days(2026, 1, 18)
        print(f"  1月営業日(1-18): {len(jan_days)}日")

        work_logs_count = 0

        for task in all_tasks:
            task_id = task["id"]
            if task_id not in task_user_map:
                continue

            user_ids = task_user_map[task_id]

            # 各担当者に対して実績を生成
            for user_id in user_ids:
                # U009は12月まで
                if user_id == 9:
                    work_days = dec_days
                else:
                    work_days = dec_days + jan_days

                for work_date in work_days:
                    # 確率的に実績を入力（70%の確率）
                    if random.random() > 0.7:
                        continue

                    # 時間は1-8時間、0.25刻み
                    base_hours = random.choice([1, 2, 3, 4, 6, 8])
                    hours = base_hours + random.choice([0, 0.25, 0.5, 0.75])

                    # 既存チェック
                    existing = conn.execute(
                        "SELECT id FROM work_log WHERE task_id=? AND user_id=? AND work_date=?",
                        (task_id, user_id, work_date.isoformat())
                    ).fetchone()

                    if existing:
                        continue

                    conn.execute(
                        "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?,?,?,?)",
                        (task_id, user_id, work_date.isoformat(), hours)
                    )
                    work_logs_count += 1

        print(f"  実績データ: {work_logs_count}件生成")

        # === 案件ステータス更新 ===
        print("\n=== ステータス更新 ===")

        # 進行中に変更
        for issue in issues:
            conn.execute(
                "UPDATE issue SET status = 'in_progress' WHERE id = ?",
                (issue["id"],)
            )
        print(f"  全案件を「進行中」に更新")

        conn.commit()
        print("\n完了!")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
