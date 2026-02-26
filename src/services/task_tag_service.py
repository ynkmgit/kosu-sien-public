"""作業タグ割当サービス

責務: 作業へのタグ付与/解除のデータ操作のみ
"""
from database import get_db


class TaskTagService:
    """作業タグ割当関連のデータ操作"""

    @staticmethod
    def get_tags_for_task(task_id: int) -> list[dict]:
        """作業に付与されたタグ一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT it.* FROM issue_tag it
                   JOIN task_tag tt ON it.id = tt.tag_id
                   WHERE tt.task_id = ?
                   ORDER BY it.sort_order ASC""",
                (task_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_task_tags_map(issue_id: int) -> dict[int, list[dict]]:
        """案件内の全作業のタグマップを取得

        Returns:
            {task_id: [tag_dict, ...]}
        """
        with get_db() as conn:
            rows = conn.execute(
                """SELECT tt.task_id, it.id, it.name, it.color, it.sort_order
                   FROM task_tag tt
                   JOIN issue_tag it ON tt.tag_id = it.id
                   JOIN task t ON tt.task_id = t.id
                   WHERE t.issue_id = ?
                   ORDER BY it.sort_order ASC""",
                (issue_id,)
            ).fetchall()
        result: dict[int, list[dict]] = {}
        for r in rows:
            task_id = r['task_id']
            if task_id not in result:
                result[task_id] = []
            result[task_id].append({
                'id': r['id'], 'name': r['name'],
                'color': r['color'], 'sort_order': r['sort_order']
            })
        return result

    @staticmethod
    def toggle(task_id: int, tag_id: int) -> bool:
        """タグ付与のトグル（存在すれば削除、なければ追加）

        Returns:
            True if tagged after toggle, False if untagged
        """
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM task_tag WHERE task_id = ? AND tag_id = ?",
                (task_id, tag_id)
            ).fetchone()

            if existing:
                conn.execute("DELETE FROM task_tag WHERE id = ?", (existing['id'],))
                return False
            else:
                conn.execute(
                    "INSERT INTO task_tag (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tag_id)
                )
                return True
