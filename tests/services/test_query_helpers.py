"""query_helpers のテスト（純粋関数、DB不要）"""
from services.query_helpers import add_in_filter, add_in_subquery_filter, validate_sort, sort_direction


class TestAddInFilter:
    def test_none_values_noop(self):
        """Noneの場合はクエリ・パラメータ変更なし"""
        params = []
        result = add_in_filter("SELECT 1", params, "col", None)
        assert result == "SELECT 1"
        assert params == []

    def test_empty_list_noop(self):
        """空リストの場合も変更なし"""
        params = []
        result = add_in_filter("SELECT 1", params, "col", [])
        assert result == "SELECT 1"
        assert params == []

    def test_single_value(self):
        params = []
        result = add_in_filter("SELECT 1 WHERE 1=1", params, "t.id", [42])
        assert "t.id IN (?)" in result
        assert params == [42]

    def test_multiple_values(self):
        params = ["existing"]
        result = add_in_filter("SELECT 1 WHERE x = ?", params, "col", [1, 2, 3])
        assert "col IN (?,?,?)" in result
        assert params == ["existing", 1, 2, 3]

    def test_chained_calls(self):
        """連続呼び出しが正しく動作"""
        params = []
        q = "SELECT 1 WHERE 1=1"
        q = add_in_filter(q, params, "a", [1])
        q = add_in_filter(q, params, "b", [2, 3])
        q = add_in_filter(q, params, "c", None)  # skip
        assert q.count("AND") == 2
        assert params == [1, 2, 3]


class TestAddInSubqueryFilter:
    def test_none_noop(self):
        params = []
        result = add_in_subquery_filter("SELECT 1", params, "x IN ({placeholders})", None)
        assert result == "SELECT 1"

    def test_with_values(self):
        params = []
        result = add_in_subquery_filter(
            "SELECT 1 WHERE 1=1", params,
            "t.id IN (SELECT id FROM tags WHERE name IN ({placeholders}))",
            ["tagA", "tagB"]
        )
        assert "name IN (?,?)" in result
        assert params == ["tagA", "tagB"]


class TestValidateSort:
    def test_valid_sort(self):
        assert validate_sort("name", {"cd", "name"}) == "name"

    def test_invalid_sort_returns_default(self):
        assert validate_sort("invalid", {"cd", "name"}) == "cd"

    def test_custom_default(self):
        assert validate_sort("invalid", {"cd", "name"}, default="name") == "name"


class TestSortDirection:
    def test_desc(self):
        assert sort_direction("desc") == "DESC"
        assert sort_direction("DESC") == "DESC"

    def test_asc(self):
        assert sort_direction("asc") == "ASC"
        assert sort_direction("anything") == "ASC"
