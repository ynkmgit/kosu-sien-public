#!/usr/bin/env python3
"""V2A9案件の全タスクに「下流」タグを付与するスクリプト

各V2A9案件にissue_tagとして「下流」を1つ作成し、
全タスクにtask_tagで紐付ける。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import get_db


def main():
    print("=" * 60)
    print("V2A9案件タスクに「下流」タグを付与")
    print("=" * 60)

    with get_db() as conn:
        # 既存タグを全クリア
        old_tt = conn.execute("DELETE FROM task_tag").rowcount
        old_it = conn.execute("DELETE FROM issue_tag").rowcount
        print(f"\n既存タグ削除: issue_tag={old_it}, task_tag={old_tt}")

        # V2A9案件を取得
        issues = conn.execute("""
            SELECT i.id, i.cd
            FROM issue i
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ-ASPIT' AND i.cd LIKE 'V2A9-%'
            ORDER BY i.cd
        """).fetchall()

        print(f"対象案件: {len(issues)}件\n")
        total_task_tags = 0

        for issue in issues:
            issue_id = issue[0]
            issue_cd = issue[1]

            # 「下流」タグを作成
            cursor = conn.execute(
                "INSERT INTO issue_tag (issue_id, name, color, sort_order) VALUES (?, ?, ?, ?)",
                (issue_id, "下流", "#6b7280", 0)
            )
            tag_id = cursor.lastrowid

            # 全タスクに紐付け
            tasks = conn.execute(
                "SELECT id FROM task WHERE issue_id = ?", (issue_id,)
            ).fetchall()
            for task in tasks:
                conn.execute(
                    "INSERT INTO task_tag (task_id, tag_id) VALUES (?, ?)",
                    (task[0], tag_id)
                )
            total_task_tags += len(tasks)
            print(f"  [{issue_cd}] 「下流」タグ → {len(tasks)}タスクに付与")

    # 検証
    print("\n" + "=" * 60)
    print("検証")
    print("=" * 60)
    with get_db() as conn:
        it_count = conn.execute("SELECT COUNT(*) FROM issue_tag").fetchone()[0]
        tt_count = conn.execute("SELECT COUNT(*) FROM task_tag").fetchone()[0]
        print(f"  issue_tag: {it_count}")
        print(f"  task_tag:  {tt_count}")

    print("\n完了!")


if __name__ == "__main__":
    main()
