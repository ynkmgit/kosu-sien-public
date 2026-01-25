"""案件サービス

責務: 案件のデータ操作のみ
"""
from database import get_db


class IssueService:
    """案件関連のデータ操作"""

    @staticmethod
    def get_all(project_id: int = None, sort: str = "cd", order: str = "asc", q: str = "") -> list[dict]:
        """案件一覧を取得"""
        allowed_sorts = {"cd", "name", "description", "status"}
        if sort not in allowed_sorts:
            sort = "cd"
        order_dir = "DESC" if order.lower() == "desc" else "ASC"

        with get_db() as conn:
            conditions = []
            params = []

            if project_id:
                conditions.append("i.project_id = ?")
                params.append(project_id)

            if q:
                like = f"%{q}%"
                conditions.append("(i.cd LIKE ? OR i.name LIKE ? OR i.description LIKE ?)")
                params.extend([like, like, like])

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            rows = conn.execute(
                f"""SELECT i.*, p.cd as project_cd, p.name as project_name,
                           ps.name as status_name
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    LEFT JOIN project_status ps ON i.project_id = ps.project_id AND i.status = ps.code
                    {where}
                    ORDER BY i.{sort} {order_dir}""",
                params
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(issue_id: int) -> dict | None:
        """案件をIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT i.*, p.cd as project_cd, p.name as project_name,
                          ps.name as status_name
                   FROM issue i
                   JOIN project p ON i.project_id = p.id
                   LEFT JOIN project_status ps ON i.project_id = ps.project_id AND i.status = ps.code
                   WHERE i.id = ?""",
                (issue_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_id_with_project(issue_id: int, project_id: int) -> dict | None:
        """案件をIDとプロジェクトIDで取得（プロジェクト所属を検証）"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM issue WHERE id = ? AND project_id = ?",
                (issue_id, project_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_list() -> list[dict]:
        """案件一覧を取得（フィルター用の最小フィールド）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT i.id, i.cd, i.name, p.cd as project_cd
                   FROM issue i
                   JOIN project p ON i.project_id = p.id
                   ORDER BY p.cd, i.cd"""
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def create(project_id: int, cd: str, name: str, status: str = "open", description: str = "") -> dict:
        """案件作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO issue (cd, project_id, name, status, description) VALUES (?, ?, ?, ?, ?)",
                (cd, project_id, name, status, description)
            )
            row = conn.execute(
                """SELECT i.*, p.cd as project_cd, p.name as project_name
                   FROM issue i
                   JOIN project p ON i.project_id = p.id
                   WHERE i.id = ?""",
                (cur.lastrowid,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def update(issue_id: int, cd: str, name: str, status: str, description: str = "") -> dict | None:
        """案件更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE issue SET cd = ?, name = ?, status = ?, description = ? WHERE id = ?",
                (cd, name, status, description, issue_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute(
                """SELECT i.*, p.cd as project_cd, p.name as project_name
                   FROM issue i
                   JOIN project p ON i.project_id = p.id
                   WHERE i.id = ?""",
                (issue_id,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def delete(issue_id: int) -> bool:
        """案件削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM issue WHERE id = ?", (issue_id,))
        return cur.rowcount > 0

    @staticmethod
    def get_estimate_total(issue_id: int) -> float:
        """案件の見積合計を取得"""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(hours), 0) FROM issue_estimate_item WHERE issue_id = ?",
                (issue_id,)
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def get_actual_total(issue_id: int) -> float:
        """案件の実績合計を取得"""
        with get_db() as conn:
            result = conn.execute(
                """SELECT COALESCE(SUM(w.hours), 0)
                   FROM task t
                   LEFT JOIN work_log w ON t.id = w.task_id
                   WHERE t.issue_id = ?""",
                (issue_id,)
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def get_status_labels(project_id: int) -> dict[str, str]:
        """プロジェクトのステータス一覧を取得（code -> name辞書）"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT code, name FROM project_status WHERE project_id = ? ORDER BY sort_order",
                (project_id,)
            ).fetchall()
        return {r['code']: r['name'] for r in rows}

    @staticmethod
    def get_estimate_totals(project_id: int) -> dict[int, float]:
        """プロジェクト内の案件ごとの見積合計を取得（issue_id -> total辞書）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT i.id, COALESCE(SUM(e.hours), 0) as total
                   FROM issue i
                   LEFT JOIN issue_estimate_item e ON i.id = e.issue_id
                   WHERE i.project_id = ?
                   GROUP BY i.id""",
                (project_id,)
            ).fetchall()
        return {r['id']: r['total'] for r in rows}

    @staticmethod
    def get_actual_totals(project_id: int) -> dict[int, float]:
        """プロジェクト内の案件ごとの実績合計を取得（issue_id -> total辞書）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT i.id, COALESCE(SUM(w.hours), 0) as total
                   FROM issue i
                   LEFT JOIN task t ON i.id = t.issue_id
                   LEFT JOIN work_log w ON t.id = w.task_id
                   WHERE i.project_id = ?
                   GROUP BY i.id""",
                (project_id,)
            ).fetchall()
        return {r['id']: r['total'] for r in rows}

    @staticmethod
    def get_all_with_totals(project_id: int, sort: str = "cd", order: str = "asc", q: str = "") -> list[dict]:
        """案件一覧を見積/実績合計付きで取得（1クエリで効率的に取得）"""
        allowed_sorts = {"cd", "name", "description", "status"}
        if sort not in allowed_sorts:
            sort = "cd"
        order_dir = "DESC" if order.lower() == "desc" else "ASC"

        with get_db() as conn:
            conditions = ["i.project_id = ?"]
            params = [project_id]

            if q:
                like = f"%{q}%"
                conditions.append("(i.cd LIKE ? OR i.name LIKE ? OR i.description LIKE ?)")
                params.extend([like, like, like])

            where = f"WHERE {' AND '.join(conditions)}"

            rows = conn.execute(
                f"""SELECT i.*, p.cd as project_cd, p.name as project_name,
                           ps.name as status_name,
                           COALESCE(est.total, 0) as estimate_total,
                           COALESCE(act.total, 0) as actual_total
                    FROM issue i
                    JOIN project p ON i.project_id = p.id
                    LEFT JOIN project_status ps ON i.project_id = ps.project_id AND i.status = ps.code
                    LEFT JOIN (
                        SELECT issue_id, SUM(hours) as total
                        FROM issue_estimate_item
                        GROUP BY issue_id
                    ) est ON i.id = est.issue_id
                    LEFT JOIN (
                        SELECT t.issue_id, SUM(w.hours) as total
                        FROM task t
                        LEFT JOIN work_log w ON t.id = w.task_id
                        GROUP BY t.issue_id
                    ) act ON i.id = act.issue_id
                    {where}
                    ORDER BY i.{sort} {order_dir}""",
                params
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def calculate_comparison(estimate: float, actual: float) -> dict:
        """見積/実績の比較データを計算（HTML生成なし）

        Returns:
            dict: {
                'estimate': float,
                'actual': float,
                'remaining': float or None,
                'rate': float or None,
                'is_overrun': bool
            }
        """
        result = {
            'estimate': estimate,
            'actual': actual,
            'remaining': None,
            'rate': None,
            'is_overrun': False,
        }
        if estimate > 0:
            result['remaining'] = estimate - actual
            result['rate'] = (actual / estimate) * 100
            result['is_overrun'] = result['remaining'] < 0
        return result
