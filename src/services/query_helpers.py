"""SQL クエリ構築ヘルパー

責務: IN句展開・ソートバリデーション等の共通パターンを DRY に提供
純粋関数のみ。DB アクセスなし。
"""


def add_in_filter(query: str, params: list, column: str, values: list | None) -> str:
    """IN句フィルターを条件付きで追加

    values が None または空なら何もしない。
    params は in-place で変更される。
    """
    if not values:
        return query
    placeholders = ",".join("?" * len(values))
    params.extend(values)
    return query + f" AND {column} IN ({placeholders})"


def add_in_subquery_filter(query: str, params: list, subquery: str, values: list | None) -> str:
    """IN句をサブクエリ付きで追加

    例: add_in_subquery_filter(q, p,
        "t.id IN (SELECT task_id FROM task_tag WHERE tag_id IN (SELECT id FROM issue_tag WHERE name IN ({placeholders})))",
        tag_names)
    """
    if not values:
        return query
    placeholders = ",".join("?" * len(values))
    params.extend(values)
    return query + " AND " + subquery.format(placeholders=placeholders)


def validate_sort(sort: str, allowed: set[str], default: str = "cd") -> str:
    """ソートカラムをバリデーション"""
    return sort if sort in allowed else default


def sort_direction(order: str) -> str:
    """ソート方向を正規化（ASC/DESC）"""
    return "DESC" if order.lower() == "desc" else "ASC"
