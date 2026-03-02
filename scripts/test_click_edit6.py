"""_sendJSON と newValue/oldValue の詳細追跡"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    # _sendJSON と _deactivateLogCell をモンキーパッチ
    page.evaluate('''() => {
        const origSend = window._sendJSON;
        window._sendJSONCalls = [];
        window._sendJSON = function(method, url, data, cell) {
            window._sendJSONCalls.push({ method, url, data });
            return origSend(method, url, data, cell);
        };

        const origDeactivate = window._deactivateLogCell;
        window._deactivateCalls = [];
        window._deactivateLogCell = function(cell, input) {
            const taskId = input.dataset.taskId;
            const userId = input.dataset.userId;
            const date = input.dataset.date;
            const key = `${taskId}-${userId}`;
            const oldValue = (workLogModel.rows[key] && workLogModel.rows[key][date]) || 0;
            const newValue = safeParseFloat(input.value);
            window._deactivateCalls.push({
                inputValue: input.value,
                newValue,
                oldValue,
                willSend: newValue !== oldValue,
                deactivating: input.dataset.deactivating || 'none'
            });
            return origDeactivate(cell, input);
        };
    }''')

    cell_el = page.query_selector('.log-cell')
    task_id = cell_el.get_attribute('data-task-id')
    user_id = cell_el.get_attribute('data-user-id')

    # クリック
    cell_el.click()
    page.wait_for_selector('.log-input')

    # fill で値をセット
    page.fill('.log-input', '5.5')

    # Enter で確定
    page.focus('.log-input')
    page.keyboard.press('Enter')
    page.wait_for_timeout(600)

    deactivate_calls = page.evaluate('() => window._deactivateCalls')
    send_calls = page.evaluate('() => window._sendJSONCalls')
    print(f'_deactivateLogCell呼び出し: {deactivate_calls}')
    print(f'_sendJSON呼び出し: {send_calls}')

    browser.close()
