"""作業ステータスサービス

責務: 案件ごとの作業ステータスのデータ操作のみ
"""
from database import get_db


class TaskStatusService:
    """作業ステータス関連のデータ操作"""

    @staticmethod
    def get_all(issue_id: int) -> list[dict]:
        """案件の作業ステータス一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM task_status WHERE issue_id = ? ORDER BY sort_order ASC",
                (issue_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_bulk(issue_ids: list[int]) -> dict[int, list[dict]]:
        """複数案件の作業ステータス一覧を一括取得"""
        if not issue_ids:
            return {}
        placeholders = ",".join("?" * len(issue_ids))
        with get_db() as conn:
            rows = conn.execute(
                f"SELECT * FROM task_status WHERE issue_id IN ({placeholders}) ORDER BY issue_id, sort_order ASC",
                issue_ids
            ).fetchall()
        result: dict[int, list[dict]] = {iid: [] for iid in issue_ids}
        for r in rows:
            result[r['issue_id']].append(dict(r))
        return result

    @staticmethod
    def get_status_labels_bulk(issue_ids: list[int]) -> dict[int, dict[str, str]]:
        """複数案件の作業ステータスラベルを一括取得"""
        if not issue_ids:
            return {}
        placeholders = ",".join("?" * len(issue_ids))
        with get_db() as conn:
            rows = conn.execute(
                f"SELECT issue_id, code, name FROM task_status WHERE issue_id IN ({placeholders}) ORDER BY sort_order",
                issue_ids
            ).fetchall()
        result: dict[int, dict[str, str]] = {iid: {} for iid in issue_ids}
        for r in rows:
            result[r['issue_id']][r['code']] = r['name']
        return result

    @staticmethod
    def get_by_id(status_id: int, issue_id: int) -> dict | None:
        """作業ステータスをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM task_status WHERE id = ? AND issue_id = ?",
                (status_id, issue_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_status_labels(issue_id: int) -> dict[str, str]:
        """案件の作業ステータス一覧を取得（code -> name辞書）"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT code, name FROM task_status WHERE issue_id = ? ORDER BY sort_order",
                (issue_id,)
            ).fetchall()
        return {r['code']: r['name'] for r in rows}

    @staticmethod
    def create(issue_id: int, code: str, name: str, sort_order: int = 0, is_done: int = 0) -> dict:
        """作業ステータス作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO task_status (issue_id, code, name, sort_order, is_done) VALUES (?, ?, ?, ?, ?)",
                (issue_id, code, name, sort_order, is_done)
            )
            row = conn.execute("SELECT * FROM task_status WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(status_id: int, issue_id: int, code: str, name: str, sort_order: int = 0, is_done: int = 0) -> dict | None:
        """作業ステータス更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE task_status SET code = ?, name = ?, sort_order = ?, is_done = ? WHERE id = ? AND issue_id = ?",
                (code, name, sort_order, is_done, status_id, issue_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM task_status WHERE id = ?", (status_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(status_id: int, issue_id: int) -> bool:
        """作業ステータス削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM task_status WHERE id = ? AND issue_id = ?",
                (status_id, issue_id)
            )
        return cur.rowcount > 0

    @staticmethod
    def resolve_ids_to_codes(status_ids: list[int]) -> list[str]:
        """作業ステータスIDリストからユニークなコードリストを取得"""
        if not status_ids:
            return []
        placeholders = ",".join("?" * len(status_ids))
        with get_db() as conn:
            rows = conn.execute(
                f"SELECT DISTINCT code FROM task_status WHERE id IN ({placeholders})",
                status_ids
            ).fetchall()
        return [r['code'] for r in rows]

    @staticmethod
    def is_in_use(status_id: int) -> bool:
        """作業ステータスが作業で使用中かチェック"""
        with get_db() as conn:
            usage = conn.execute(
                "SELECT COUNT(*) FROM task t JOIN task_status ts ON t.status = ts.code AND t.issue_id = ts.issue_id WHERE ts.id = ?",
                (status_id,)
            ).fetchone()[0]
        return usage > 0
