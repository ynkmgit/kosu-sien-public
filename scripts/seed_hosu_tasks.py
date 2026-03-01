#!/usr/bin/env python3
"""保守(help-XXXXX)案件に調査・改修タスクを登録するスクリプト"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import get_db

TASK_TEMPLATE = [
    {"cd": "T01", "name": "調査", "sort": 10},
    {"cd": "T02", "name": "改修", "sort": 20},
]


def main():
    print("=" * 60)
    print("保守 help-XXXXX 案件にタスク登録")
    print("=" * 60)

    with get_db() as conn:
        issues = conn.execute("""
            SELECT i.id, i.cd, i.name
            FROM issue i
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ-HOSU' AND i.cd LIKE 'help-%'
            ORDER BY i.cd
        """).fetchall()

        print(f"\n対象案件: {len(issues)}件")
        total = 0

        for issue in issues:
            issue_id = issue[0]
            issue_cd = issue[1]

            existing = conn.execute(
                "SELECT COUNT(*) FROM task WHERE issue_id = ?", (issue_id,)
            ).fetchone()[0]
            if existing > 0:
                print(f"  [{issue_cd}] スキップ（既存タスク{existing}件）")
                continue

            for t in TASK_TEMPLATE:
                conn.execute(
                    "INSERT INTO task (cd, issue_id, name, sort_order) VALUES (?, ?, ?, ?)",
                    (t["cd"], issue_id, t["name"], t["sort"])
                )
            total += len(TASK_TEMPLATE)
            print(f"  [{issue_cd}] {issue[2]} → 調査・改修 登録")

    print(f"\n登録タスク合計: {total}")
    print("完了!")


if __name__ == "__main__":
    main()
