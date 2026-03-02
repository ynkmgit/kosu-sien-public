"""実績入力のclick-to-edit詳細デバッグ"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # コンソールログを全て記録
    console_logs = []
    page.on('console', lambda msg: console_logs.append(f'[{msg.type}] {msg.text}'))

    # ネットワークリクエストを全て記録
    requests = []
    page.on('request', lambda req: requests.append({'url': req.url.replace('http://localhost:8001', ''), 'method': req.method}))

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    # workLogModelの状態確認
    model_state = page.evaluate('''() => {
        return {
            initialized: workLogModel.initialized,
            rowCount: workLogModel.rowKeys.length,
            dateCount: workLogModel.dateKeys.length,
        };
    }''')
    print(f'workLogModel状態: {model_state}')

    cells = page.query_selector_all('.log-cell')
    print(f'log-cell数: {len(cells)}')

    if cells:
        cell = cells[0]
        task_id = cell.get_attribute('data-task-id')
        user_id = cell.get_attribute('data-user-id')
        date = cell.get_attribute('data-date')
        print(f'対象: task_id={task_id}, user_id={user_id}, date={date}')

        # 現在のモデル内の値を確認
        old_model_val = page.evaluate(f'''() => {{
            const key = "{task_id}-{user_id}";
            return workLogModel.rows[key] ? workLogModel.rows[key]["{date}"] : "key not found";
        }}''')
        print(f'モデル内の現在値: {old_model_val}')

        # セルをクリック
        cell.click()
        page.wait_for_selector('.log-input', timeout=2000)
        inp = page.query_selector('.log-input')

        inp_val = inp.get_attribute('value') if inp else None
        print(f'input出現, 初期value属性: {inp_val}')

        # fill で値をセット（type より確実）
        page.fill('.log-input', '9.75')
        actual_val = page.evaluate('() => document.querySelector(".log-input")?.value')
        print(f'fill後のinput.value: {actual_val}')

        # Enter押下
        page.keyboard.press('Enter')
        page.wait_for_timeout(800)

        # input が消えたか
        inp_after = page.query_selector('.log-input')
        print(f'Enter後にinputが消えた: {inp_after is None}')

        # POST /work-logs があるか
        post_reqs = [r for r in requests if 'work-logs' in r['url'] and r['method'] == 'POST']
        print(f'POST /work-logs: {post_reqs}')
        print(f'全リクエスト: {[r for r in requests if r["method"] != "GET"]}')

        # コンソールエラー
        errors = [l for l in console_logs if '[error]' in l.lower() or 'Error' in l]
        print(f'コンソールエラー: {errors}')
        print(f'全コンソールログ: {console_logs[:20]}')

    browser.close()
