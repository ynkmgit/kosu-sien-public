"""実績入力のclick-to-edit修正後の動作確認"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # ネットワークリクエストを記録
    captured = []
    page.on('request', lambda req: captured.append({'url': req.url, 'method': req.method})
            if '/work-logs' in req.url else None)

    page.goto('http://localhost:8001/work-logs')
    page.wait_for_load_state('networkidle')

    # log-cell を探す
    cells = page.query_selector_all('.log-cell')
    print(f'log-cell数: {len(cells)}')

    if cells:
        cell = cells[0]
        task_id = cell.get_attribute('data-task-id')
        user_id = cell.get_attribute('data-user-id')
        date = cell.get_attribute('data-date')
        original_text = cell.text_content().strip()
        print(f'対象セル: task_id={task_id}, user_id={user_id}, date={date}, 現在値="{original_text}"')

        # セルをクリックして input を出す
        cell.click()
        page.wait_for_selector('.log-input', timeout=2000)
        inp = page.query_selector('.log-input')
        print(f'input出現: {inp is not None}')

        # 値を入力してEnterキー
        inp.click(click_count=3)
        inp.type('2.5')
        print(f'入力後のinput.value: {inp.input_value()}')
        inp.press('Enter')

        # 少し待ってfetchが飛ぶか確認
        page.wait_for_timeout(500)

        # inputが消えたか
        inp_after = page.query_selector('.log-input')
        print(f'Enter後にinputが消えた: {inp_after is None}')

        print(f'キャプチャしたリクエスト: {captured}')

        # リロードして値が保存されているか確認
        page.reload()
        page.wait_for_load_state('networkidle')
        cells2 = page.query_selector_all(f'.log-cell[data-task-id="{task_id}"][data-user-id="{user_id}"][data-date="{date}"]')
        if cells2:
            saved = cells2[0].text_content().strip()
            print(f'リロード後の値: "{saved}"')
        else:
            print('リロード後にセルが見つからない')
    else:
        print('log-cellが見つかりません。スクリーンショットを確認してください。')
        page.screenshot(path='/tmp/no_cells.png', full_page=True)

    browser.close()
