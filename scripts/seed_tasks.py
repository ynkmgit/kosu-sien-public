#!/usr/bin/env python3
"""V2A9案件に標準タスクテンプレートを登録するスクリプト

案件スケジュール管理テンプレートから抽出した
ASPIT開発の標準ワークフローをタスクとして登録する。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from database import get_db

# 標準タスクテンプレート（工程 → タスク一覧）
# sort_order でテンプレート内の順番を管理
TASK_TEMPLATE = [
    # 仕様検討
    {"cd": "T01", "name": "仕様検討", "sort": 10},

    # 単体工程
    {"cd": "T02", "name": "詳細仕様書設計", "sort": 20},
    {"cd": "T03", "name": "詳細仕様書セルフチェック", "sort": 21},
    {"cd": "T04", "name": "単体テスト仕様書設計", "sort": 30},
    {"cd": "T05", "name": "単体テスト仕様書セルフチェック", "sort": 31},
    {"cd": "T06", "name": "製造・動作確認", "sort": 40},
    {"cd": "T07", "name": "単体テスト", "sort": 50},
    {"cd": "T08", "name": "単体工程 戻り対応", "sort": 55},

    # 結合工程
    {"cd": "T09", "name": "結合テスト仕様書設計", "sort": 60},
    {"cd": "T10", "name": "結合テスト仕様書セルフチェック", "sort": 61},
    {"cd": "T11", "name": "結合テスト実施", "sort": 70},
    {"cd": "T12", "name": "結合工程 戻り対応", "sort": 75},

    # テストリリース
    {"cd": "T13", "name": "テストリリース準備・作業・動作確認", "sort": 80},
    {"cd": "T14", "name": "テストリリース後対応", "sort": 85},

    # 本番リリース
    {"cd": "T15", "name": "本番リリース準備・作業", "sort": 90},
    {"cd": "T16", "name": "本番リリース後対応（不具合以外）", "sort": 95},
    {"cd": "T17", "name": "不具合対応", "sort": 100},
]


def main():
    print("=" * 60)
    print("V2A9案件に標準タスクテンプレートを登録")
    print("=" * 60)

    with get_db() as conn:
        # PJ-ASPITのV2A9案件を取得
        rows = conn.execute("""
            SELECT i.id, i.cd, i.name
            FROM issue i
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ-ASPIT' AND i.cd LIKE 'V2A9-%'
            ORDER BY i.cd
        """).fetchall()

        print(f"\n対象案件: {len(rows)}件")

        total_tasks = 0
        for row in rows:
            issue_id = row[0]
            issue_cd = row[1]
            issue_name = row[2]

            # 既存タスクがあればスキップ
            existing = conn.execute(
                "SELECT COUNT(*) FROM task WHERE issue_id = ?",
                (issue_id,)
            ).fetchone()[0]
            if existing > 0:
                print(f"  [{issue_cd}] スキップ（既存タスク{existing}件）")
                continue

            # タスク登録
            for t in TASK_TEMPLATE:
                conn.execute(
                    "INSERT INTO task (cd, issue_id, name, sort_order) VALUES (?, ?, ?, ?)",
                    (t["cd"], issue_id, t["name"], t["sort"])
                )
            total_tasks += len(TASK_TEMPLATE)
            print(f"  [{issue_cd}] {issue_name} → {len(TASK_TEMPLATE)}タスク登録")

    # 検証
    print("\n" + "=" * 60)
    print("検証")
    print("=" * 60)
    with get_db() as conn:
        task_count = conn.execute("SELECT COUNT(*) FROM task").fetchone()[0]
        v2a9_issues = conn.execute("""
            SELECT COUNT(DISTINCT i.id)
            FROM issue i
            JOIN project p ON i.project_id = p.id
            WHERE p.cd = 'PJ-ASPIT' AND i.cd LIKE 'V2A9-%'
        """).fetchone()[0]
        print(f"  V2A9案件数:     {v2a9_issues}")
        print(f"  登録タスク合計: {task_count}")
        print(f"  今回登録:       {total_tasks}")

    print("\n完了!")


if __name__ == "__main__":
    main()
