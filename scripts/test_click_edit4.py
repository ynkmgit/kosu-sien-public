"""実際のブラウザ操作でのclick-to-edit最終確認"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    requests = []
    page.on('request', lambda req: requests.append({'url': req.url.replace('http://localhost:8001', ''), 'method': req.method})
            if '/work-logs' in req.url and req.method == 'POST' else None)

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    # locator を使って確実に操作
    cell_el = page.query_selector('.log-cell')

    # 現在の値を取得
    task_id = cell_el.get_attribute('data-task-id')
    user_id = cell_el.get_attribute('data-user-id')
    date = cell_el.get_attribute('data-date')
    current_text = cell_el.text_content().strip()
    print(f'セル: task_id={task_id}, user_id={user_id}, date={date}, 現在値="{current_text}"')

    # クリックして input を出す
    cell_el.click()
    page.wait_for_selector('.log-input', timeout=2000)
    print('input OK')

    # locator で fill してから press
    page.fill('.log-input', '4.5')
    iv = page.evaluate('() => document.querySelector(".log-input")?.value')
    print(f'input.value after fill: {iv}')

    # Enter で確定（input にフォーカスして Enter）
    page.focus('.log-input')
    page.keyboard.press('Enter')
    page.wait_for_timeout(600)

    # inputが消えたか
    inp_after = page.query_selector('.log-input')
    print(f'Enter後のinput: {inp_after}')

    # POSTが飛んだか
    print(f'POST /work-logs: {requests}')

    # セルの表示が更新されたか
    cell_text_after = page.query_selector(f'.log-cell[data-task-id="{task_id}"][data-user-id="{user_id}"][data-date="{date}"]')
    print(f'セルの表示（Enter後）: "{cell_text_after.text_content().strip() if cell_text_after else "N/A"}"')

    # リロードして保存確認
    page.reload()
    page.wait_for_load_state('networkidle')
    saved_el = page.query_selector(f'.log-cell[data-task-id="{task_id}"][data-user-id="{user_id}"][data-date="{date}"]')
    print(f'リロード後の値: "{saved_el.text_content().strip() if saved_el else "N/A"}"')

    browser.close()
