/**
 * オートコンプリート共通モジュール
 *
 * 使用方法:
 *   handleAutocomplete(input, type)     - 検索実行
 *   hideAutocomplete(type)              - ドロップダウン非表示
 *   selectAutocomplete(type, id, label) - 候補選択（各画面でオーバーライド可能）
 *   getSelectedIds(type)                - 選択済みID取得（URLパラメータから）
 *
 * 各画面で必要に応じてselectAutocomplete()をオーバーライドするか、
 * addFilter(type, id)関数を定義してください。
 */

let autocompleteTimeout = null;

/**
 * オートコンプリート検索を実行
 * @param {HTMLInputElement} input - 入力要素
 * @param {string} type - エンティティタイプ（user, project, issue等）
 */
function handleAutocomplete(input, type) {
    const dropdown = document.getElementById('autocomplete-' + type);
    if (!dropdown) return;

    const query = input.value.trim();
    const excludeIds = getSelectedIds(type);

    clearTimeout(autocompleteTimeout);
    autocompleteTimeout = setTimeout(() => {
        const excludeParams = excludeIds.map(id => 'exclude=' + id).join('&');
        const url = `/search/${type}s?q=${encodeURIComponent(query)}&${excludeParams}`;

        fetch(url)
            .then(res => res.text())
            .then(html => {
                dropdown.innerHTML = html;
                dropdown.classList.add('show');
            });
    }, 150);
}

/**
 * ドロップダウンを非表示
 * @param {string} type - エンティティタイプ
 */
function hideAutocomplete(type) {
    const dropdown = document.getElementById('autocomplete-' + type);
    if (dropdown) dropdown.classList.remove('show');
}

/**
 * 選択済みIDを取得（URLパラメータから）
 * @param {string} type - エンティティタイプ
 * @returns {number[]} 選択済みIDの配列
 */
function getSelectedIds(type) {
    const url = new URL(window.location.href);
    return url.searchParams.getAll(type).map(Number);
}

/**
 * 候補を選択
 * 各画面でaddFilter()を定義するか、この関数をオーバーライドしてください
 * @param {string} type - エンティティタイプ
 * @param {number} id - 選択したID
 * @param {string} label - 表示ラベル（参考用）
 */
function selectAutocomplete(type, id, label) {
    if (typeof addFilter === 'function') {
        addFilter(type, id);
    }
}
