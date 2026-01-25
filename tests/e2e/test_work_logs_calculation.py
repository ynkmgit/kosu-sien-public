"""実績入力の計算列リアルタイム更新E2Eテスト"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def setup_test_data(page: Page, base_url: str):
    """テストデータのセットアップ"""
    # プロジェクト作成
    page.goto(f"{base_url}/projects")
    page.fill("input[name='cd']", "TEST01")
    page.fill("input[name='name']", "テストプロジェクト")
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)

    # 案件作成
    page.click("a:has-text('テストプロジェクト')")
    page.wait_for_timeout(300)
    page.click("a:has-text('案件')")
    page.wait_for_timeout(300)
    page.fill("input[name='cd']", "I001")
    page.fill("input[name='name']", "テスト案件")
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)

    # 作業作成
    page.click("a:has-text('テスト案件')")
    page.wait_for_timeout(300)
    page.click("a:has-text('作業')")
    page.wait_for_timeout(300)
    page.fill("input[name='cd']", "T001")
    page.fill("input[name='name']", "テスト作業")
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)

    # 担当割当
    page.goto(f"{base_url}/task-assignees")
    page.wait_for_timeout(500)

    # ユーザーとタスクを選択（既存データを使用）
    page.select_option("select[name='user_id']", index=1)
    page.select_option("select[name='task_id']", index=1)
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)


def test_work_logs_realtime_calculation(page: Page, base_url: str, setup_test_data):
    """実績入力のリアルタイム計算テスト"""
    # 実績入力画面へ移動
    page.goto(f"{base_url}/work-logs?view=week")
    page.wait_for_timeout(1000)

    # グリッドが表示されるまで待機
    page.wait_for_selector(".log-table, .week-table", timeout=5000)

    # 初期状態の確認（すべて0または空）
    grand_total = page.locator(".grand-total").text_content()
    assert grand_total in ["0.0h", "-", ""], f"初期状態の総合計が想定外: {grand_total}"

    # 最初のセルに値を入力
    first_input = page.locator(".log-input").first
    first_input.fill("2.5")
    first_input.blur()  # フォーカスを外す

    # JavaScriptの計算が完了するまで少し待機
    page.wait_for_timeout(200)

    # 行合計が更新されているか確認
    row_total = page.locator(".row-total").first.text_content()
    assert "2.5" in row_total or "2.50" in row_total, f"行合計が更新されていない: {row_total}"

    # 列合計が更新されているか確認
    col_total = page.locator(".col-total").first.text_content()
    assert col_total in ["2.5", "2.50"], f"列合計が更新されていない: {col_total}"

    # 総合計が更新されているか確認
    grand_total = page.locator(".grand-total").text_content()
    assert "2.5" in grand_total, f"総合計が更新されていない: {grand_total}"


def test_estimate_realtime_calculation(page: Page, base_url: str, setup_test_data):
    """案件見積のリアルタイム計算テスト"""
    # プロジェクト詳細から案件見積へ
    page.goto(f"{base_url}/projects")
    page.wait_for_timeout(500)
    page.click("a:has-text('テストプロジェクト')")
    page.wait_for_timeout(300)
    page.click("a:has-text('案件')")
    page.wait_for_timeout(300)
    page.click("a:has-text('テスト案件')")
    page.wait_for_timeout(300)
    page.click("a:has-text('見積内訳')")
    page.wait_for_timeout(500)

    # 初期状態の合計確認
    total = page.locator(".total-row td").nth(1).text_content()
    initial_total = float(total) if total and total != "-" else 0.0

    # 見積項目を追加
    page.fill("input[name='name']", "設計")
    page.fill("input[name='hours']", "8.5")
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)

    # 合計が更新されているか確認
    total = page.locator(".total-row td").nth(1).text_content()
    expected = initial_total + 8.5
    assert total == f"{expected:.2f}", f"合計が更新されていない: {total}, 期待値: {expected:.2f}"

    # もう一つ追加
    page.fill("input[name='name']", "実装")
    page.fill("input[name='hours']", "16.25")
    page.click("button:has-text('追加')")
    page.wait_for_timeout(500)

    # 合計が再度更新されているか確認
    total = page.locator(".total-row td").nth(1).text_content()
    expected = initial_total + 8.5 + 16.25
    assert total == f"{expected:.2f}", f"合計が更新されていない: {total}, 期待値: {expected:.2f}"


def test_monthly_assignment_realtime_calculation(page: Page, base_url: str):
    """月次アサイン（簡易モード）のリアルタイム計算テスト"""
    # 月次アサイン画面へ移動（簡易モード）
    page.goto(f"{base_url}/monthly-assignments?mode=simple")
    page.wait_for_timeout(1000)

    # グリッドが表示されるまで待機
    page.wait_for_selector(".assign-table", timeout=5000)

    # 最初のセルに値を入力
    first_input = page.locator(".assign-input").first
    first_input.fill("40")
    first_input.blur()

    # JavaScriptの計算が完了するまで少し待機
    page.wait_for_timeout(200)

    # 行合計が更新されているか確認
    row_total = page.locator(".row-total .total-hours").first.text_content()
    assert "40" in row_total, f"行合計が更新されていない: {row_total}"

    # MM表示が更新されているか確認
    mm_display = page.locator(".row-total .total-mm").first.text_content()
    assert "0.25MM" in mm_display, f"MM表示が更新されていない: {mm_display}"

    # 列合計が更新されているか確認
    col_total = page.locator(".col-total").first.text_content()
    assert "40" in col_total, f"列合計が更新されていない: {col_total}"

    # もう一つのセルに入力
    second_input = page.locator(".assign-input").nth(1)
    second_input.fill("80")
    second_input.blur()
    page.wait_for_timeout(200)

    # 総合計が更新されているか確認
    grand_total = page.locator(".grand-total").text_content()
    assert "120" in grand_total, f"総合計が更新されていない: {grand_total}"


def test_multiple_inputs_calculation(page: Page, base_url: str, setup_test_data):
    """複数セル入力時の計算テスト"""
    page.goto(f"{base_url}/work-logs?view=week")
    page.wait_for_timeout(1000)
    page.wait_for_selector(".log-table, .week-table", timeout=5000)

    # 複数のセルに値を入力
    inputs = page.locator(".log-input")
    count = min(inputs.count(), 5)  # 最大5セル

    total_expected = 0.0
    for i in range(count):
        value = (i + 1) * 1.25  # 1.25, 2.5, 3.75, 5.0, 6.25
        inputs.nth(i).fill(str(value))
        inputs.nth(i).blur()
        total_expected += value
        page.wait_for_timeout(100)

    # 総合計が正しいか確認
    page.wait_for_timeout(300)
    grand_total = page.locator(".grand-total").text_content()
    assert f"{total_expected:.1f}" in grand_total, f"総合計が不正: {grand_total}, 期待値: {total_expected:.1f}h"
