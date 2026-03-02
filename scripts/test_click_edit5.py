"""_deactivateLogCell の呼び出しを追跡"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    requests = []
    page.on('request', lambda req: requests.append({'url': req.url.replace('http://localhost:8001', ''), 'method': req.method})
            if 'work-logs' in req.url and req.method == 'POST' else None)

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    # _deactivateLogCell をモンキーパッチして呼び出しを記録
    page.evaluate('''() => {
        const orig = window._deactivateLogCell;
        window._deactivateLogCalls = [];
        window._deactivateLogCell = function(cell, input) {
            window._deactivateLogCalls.push({
                deactivating: input.dataset.deactivating || 'none',
                inputValue: input.value,
                time: Date.now()
            });
            return orig(cell, input);
        };
    }''')

    cell_el = page.query_selector('.log-cell')
    task_id = cell_el.get_attribute('data-task-id')
    user_id = cell_el.get_attribute('data-user-id')
    date = cell_el.get_attribute('data-date')
    print(f'セル: task_id={task_id}, user_id={user_id}, date={date}')

    # クリック
    cell_el.click()
    page.wait_for_selector('.log-input')

    # fill で値をセット
    page.fill('.log-input', '5.5')
    page.wait_for_timeout(100)

    calls_after_fill = page.evaluate('() => window._deactivateLogCalls')
    print(f'fill後の_deactivateLogCell呼び出し: {calls_after_fill}')

    # Enter でセル確定
    page.focus('.log-input')
    page.keyboard.press('Enter')
    page.wait_for_timeout(600)

    calls_after_enter = page.evaluate('() => window._deactivateLogCalls')
    print(f'Enter後の_deactivateLogCell呼び出し: {calls_after_enter}')
    print(f'POST: {requests}')

    browser.close()
