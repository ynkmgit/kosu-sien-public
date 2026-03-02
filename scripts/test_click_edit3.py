"""JS内でfetchをモンキーパッチして直接動作確認"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    result = page.evaluate('''() => {
        // fetchをモンキーパッチして記録
        const captured = [];
        const origFetch = window.fetch;
        window.fetch = async (url, opts) => {
            captured.push({ url: String(url), method: opts?.method || 'GET', body: opts?.body ? JSON.stringify(opts.body) : null });
            return origFetch(url, opts);
        };

        // セルを取得
        const cell = document.querySelector('.log-cell');
        if (!cell) return { error: 'no log-cell' };

        const taskId = cell.dataset.taskId;
        const userId = cell.dataset.userId;
        const date = cell.dataset.date;
        const oldModel = workLogModel.rows[`${taskId}-${userId}`]?.[date];

        // _activateLogCellを呼ぶ（クリックと同等）
        _activateLogCell(cell);
        const input = cell.querySelector('.log-input');
        if (!input) return { error: 'input not created', cellHTML: cell.outerHTML };

        const inputVal = input.value;

        // 値を変更（現在値と明確に異なる値）
        input.value = '99.0';

        // _deactivateLogCellを直接呼ぶ（blur相当）
        _deactivateLogCell(cell, input);

        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    taskId, userId, date, oldModel, inputVal,
                    captured,
                    newModel: workLogModel.rows[`${taskId}-${userId}`]?.[date],
                });
            }, 400);
        });
    }''')

    print(f'結果: {result}')

    browser.close()
