"""ルーター共通機能

後方互換性のため、全関数・変数を再エクスポート。
既存の `from .common import ...` がそのまま動作。
"""

# core.py - 基本ユーティリティ
from .core import (
    templates,
    build_filter_query,
    get_project_or_404,
    get_issue_or_404,
    get_user_or_404,
    get_attribute_type_or_404,
    validate_sort_params,
    get_rate_class,
    build_like_params,
)

# dates.py - 日付関連
from .dates import (
    get_current_month,
    parse_month,
    get_prev_next_month,
    WEEKDAY_NAMES,
    get_week_dates,
    get_prev_next_week,
    get_week_range_str,
    parse_week_date,
)

# filters.py - フィルターUI
from .filters import (
    render_filter_tags,
    render_filter_options,
    render_filter_group,
    render_autocomplete_filter_group,
    render_view_toggle,
)

# renders.py - レンダリング
from .renders import (
    render_log_cell,
    render_progress_cell,
    render_row_label,
    render_edit_actions,
    render_sortable_th,
)

__all__ = [
    # core
    "templates",
    "build_filter_query",
    "get_project_or_404",
    "get_issue_or_404",
    "get_user_or_404",
    "get_attribute_type_or_404",
    "validate_sort_params",
    "get_rate_class",
    "build_like_params",
    # dates
    "get_current_month",
    "parse_month",
    "get_prev_next_month",
    "WEEKDAY_NAMES",
    "get_week_dates",
    "get_prev_next_week",
    "get_week_range_str",
    "parse_week_date",
    # filters
    "render_filter_tags",
    "render_filter_options",
    "render_filter_group",
    "render_autocomplete_filter_group",
    "render_view_toggle",
    # renders
    "render_log_cell",
    "render_progress_cell",
    "render_row_label",
    "render_edit_actions",
    "render_sortable_th",
]
