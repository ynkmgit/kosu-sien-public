#!/usr/bin/env python3
"""ASPITPJ V2A9案件のwork_logを登録するスクリプト

_worklog_aspit.jsonのデータをDBに投入する。
各案件の工数は全タスクに均等割りする。
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import get_db

DATA_PATH = PROJECT_ROOT / "sample" / "_worklog_aspit.json"

# Excel担当者名 → DBユーザー名 マッピング
USER_MAP = {
    "田村":     "田村清貴",
    "田坂":     "田坂基樹",
    "吉村(武)": "吉村武志",
    "西野":     "西野真由美",
    "横尾":     "横尾梓",
    "廣瀬":     "廣瀬勇次",
    "田中(弘)": "田中弘臣",
    "山下":     "山下栞奈",
    "川村":     "川村颯",
    "森口":     "森口祥子",
    "BP中間":   "中間祐作",
    "松本":     "松本佳乃",
    "高柳":     "高柳光希",
    "鷺山":     "鷺山見法",
    "堺":       "堺絵理香",
    "吉田":     "吉田",
    "川﨑":     "川﨑初音",
    "藤原":     "藤原",
    "BP力久":   "力久",
}


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 60)
    print("ASPITPJ work_log 登録")
    print("=" * 60)

    with get_db() as conn:
        # ユーザー名→IDマップ
        user_rows = conn.execute("SELECT id, name FROM user").fetchall()
        user_id_map = {r[1]: r[0] for r in user_rows}

        total_logs = 0
        skipped_users = set()

        for sec in data:
            issue_cd = sec["issue_cd"]

            # 案件ID取得
            issue_row = conn.execute(
                "SELECT i.id FROM issue i JOIN project p ON i.project_id = p.id WHERE p.cd = 'PJ-ASPIT' AND i.cd = ?",
                (issue_cd,)
            ).fetchone()
            if not issue_row:
                print(f"  [{issue_cd}] 案件なし - スキップ")
                continue
            issue_id = issue_row[0]

            # タスク一覧取得（均等割り用）
            tasks = conn.execute(
                "SELECT id FROM task WHERE issue_id = ? ORDER BY sort_order",
                (issue_id,)
            ).fetchall()
            if not tasks:
                print(f"  [{issue_cd}] タスクなし - スキップ")
                continue
            task_ids = [t[0] for t in tasks]
            num_tasks = len(task_ids)

            issue_logs = 0
            for entry in sec["entries"]:
                excel_name = entry["user"]
                db_name = USER_MAP.get(excel_name)
                if not db_name:
                    skipped_users.add(excel_name)
                    continue
                user_id = user_id_map.get(db_name)
                if not user_id:
                    skipped_users.add(excel_name)
                    continue

                total_hours = entry["hours"]
                date_str = entry["date"]

                # 均等割り
                hours_per_task = round(total_hours / num_tasks, 2)
                remainder = round(total_hours - hours_per_task * num_tasks, 2)

                for i, task_id in enumerate(task_ids):
                    h = hours_per_task
                    if i == 0:
                        h = round(h + remainder, 2)
                    if h <= 0:
                        continue
                    conn.execute(
                        "INSERT OR IGNORE INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, ?, ?)",
                        (task_id, user_id, date_str, h)
                    )
                    issue_logs += 1

            total_logs += issue_logs
            if issue_logs > 0:
                print(f"  [{issue_cd}] {issue_logs} work_logs")

        if skipped_users:
            print(f"\n  未マッチ担当者: {skipped_users}")

    # 検証
    print("\n" + "=" * 60)
    print("検証")
    print("=" * 60)
    with get_db() as conn:
        wl_count = conn.execute("SELECT COUNT(*) FROM work_log").fetchone()[0]
        wl_hours = conn.execute("SELECT COALESCE(SUM(hours), 0) FROM work_log").fetchone()[0]
        print(f"  work_log: {wl_count}件")
        print(f"  合計工数: {wl_hours}h")

    print(f"\n今回登録: {total_logs}件")
    print("完了!")


if __name__ == "__main__":
    main()
