"""フィルターUI部品

責務: フィルター関連のHTML生成
"""
from html import escape


def render_filter_tags(items, selected_ids: list[int], type_name: str) -> str:
    """選択済みアイテムのタグHTML生成"""
    tags = ""
    for item in items:
        if item['id'] in selected_ids:
            tags += f'''<span class="filter-tag" data-type="{type_name}" data-id="{item['id']}">
                {escape(item['name'])}
                <button type="button" class="tag-remove" onclick="removeFilter('{type_name}', {item['id']})">×</button>
            </span>'''
    return tags


def render_filter_options(items, selected_ids: list[int]) -> str:
    """未選択アイテムのselect option HTML生成"""
    return "".join(
        f'<option value="{item["id"]}">{escape(item["cd"])} {escape(item["name"])}</option>'
        for item in items if item['id'] not in selected_ids
    )


def render_filter_group(label: str, tags: str, options: str, type_name: str) -> str:
    """フィルターグループHTML生成（従来のドロップダウン方式）"""
    return f'''<div class="filter-group">
        <label class="filter-label">{label}</label>
        <div class="filter-tags">{tags}</div>
        <select class="filter-select" onchange="addFilter('{type_name}', this.value)">
            <option value="">+ 追加...</option>
            {options}
        </select>
    </div>'''


def render_autocomplete_filter_group(label: str, tags: str, type_name: str, placeholder: str = "検索...") -> str:
    """オートコンプリート付きフィルターグループHTML生成"""
    return f'''<div class="filter-group">
        <label class="filter-label">{label}</label>
        <div class="filter-tags">{tags}</div>
        <div class="autocomplete-wrapper">
            <input type="text" class="autocomplete-input" data-type="{type_name}"
                   placeholder="{placeholder}" autocomplete="off"
                   oninput="handleAutocomplete(this, '{type_name}')"
                   onfocus="handleAutocomplete(this, '{type_name}')"
                   onblur="setTimeout(() => hideAutocomplete('{type_name}'), 200)">
            <div class="autocomplete-dropdown" id="autocomplete-{type_name}"></div>
        </div>
    </div>'''


def render_view_toggle(current_view: str) -> str:
    """表示切替ボタンHTML生成"""
    week_class = "btn-primary" if current_view == "week" else "btn-ghost"
    month_class = "btn-primary" if current_view == "month" else "btn-ghost"
    return f'''<div class="view-toggle">
        <a href="javascript:void(0)" onclick="changeView('week')" class="btn {week_class} btn-sm">週</a>
        <a href="javascript:void(0)" onclick="changeView('month')" class="btn {month_class} btn-sm">月</a>
    </div>'''
