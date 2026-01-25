"""ユーザー画面E2Eテスト"""
import pytest


class TestUserPage:
    """ページ表示テスト"""

    def test_page_loads(self, page, base_url):
        """ページが正常に読み込まれる"""
        page.goto(f"{base_url}/users")
        assert "ユーザー管理" in page.title()

    def test_list_displays_users(self, page, base_url):
        """ユーザー一覧が表示される"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")
        assert page.locator("text=U001").is_visible()
        assert page.locator("text=U002").is_visible()


class TestUserSort:
    """ソート機能テスト"""

    def test_sort_toggle_changes_icon(self, page, base_url):
        """ソートクリックでアイコンが変わる"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # CDヘッダーをクリック（降順に）
        page.click("th.sortable:has-text('CD')")
        page.wait_for_selector("th:has-text('CD') >> text=▼")

        # 降順アイコンを確認
        assert page.locator("th:has-text('CD') >> text=▼").is_visible()

    def test_sort_desc_reverses_order(self, page, base_url):
        """降順ソートで順序が逆になる"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # CDヘッダーをクリック（降順に）
        page.click("th.sortable:has-text('CD')")
        page.wait_for_selector("th:has-text('CD') >> text=▼")

        # tbody内のテキストを取得して順序確認
        content = page.locator("tbody").inner_text()
        # U002がU001より前にあることを確認
        assert content.index("U002") < content.index("U001")


class TestUserSearch:
    """検索機能テスト"""

    def test_search_filters_results(self, page, base_url):
        """検索で結果が絞り込まれる"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # 検索（CDで検索）
        search_input = page.locator("input[name='q']")
        search_input.click()
        search_input.type("U001", delay=50)
        page.wait_for_function("document.querySelectorAll('tbody tr').length === 1")

        # U001のみ表示（tbody内で確認）
        tbody_text = page.locator("tbody").inner_text()
        assert "U001" in tbody_text
        assert "U002" not in tbody_text

    def test_search_clear_shows_all(self, page, base_url):
        """検索クリアで全件表示"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # 検索して絞り込み
        search_input = page.locator("input[name='q']")
        search_input.click()
        search_input.type("U001", delay=50)
        page.wait_for_function("document.querySelectorAll('tbody tr').length === 1")

        # 検索クリア
        search_input.fill("")
        search_input.press("Backspace")
        page.wait_for_selector("text=U002")

        # 全件表示
        assert page.locator("text=U001").is_visible()
        assert page.locator("text=U002").is_visible()


class TestUserEdit:
    """編集機能テスト"""

    def test_edit_button_shows_form(self, page, base_url):
        """編集ボタンで編集フォームが表示される"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # 編集ボタンクリック
        page.click("tr:has-text('U001') button")
        page.wait_for_selector("input.edit-input")

        # 編集用入力フィールドが表示される
        assert page.locator("input.edit-input").first.is_visible()

    def test_edit_save_updates_row(self, page, base_url):
        """編集保存で行が更新される"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # 編集モードに
        page.click("tr:has-text('U001') button")
        page.wait_for_selector("input.edit-input")

        # 名前を変更
        name_input = page.locator("tr:has-text('U001') input[name='name']")
        name_input.fill("更新太郎")

        # 保存
        page.click("tr:has-text('U001') button.btn-success")
        page.wait_for_selector("text=更新太郎")

        # 更新確認
        assert page.locator("text=更新太郎").is_visible()

        # 元に戻す
        page.click("tr:has-text('更新太郎') button")
        page.wait_for_selector("input.edit-input")
        name_input = page.locator("tr:has-text('更新太郎') input[name='name']")
        name_input.fill("田中太郎")
        page.click("tr:has-text('更新太郎') button.btn-success")
        page.wait_for_selector("text=田中太郎")

    def test_edit_cancel_restores_row(self, page, base_url):
        """編集取消で元の行に戻る"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # 編集モードに
        page.click("tr:has-text('U001') button")
        page.wait_for_selector("input.edit-input")

        # 名前を変更（保存しない）
        name_input = page.locator("tr:has-text('U001') input[name='name']")
        name_input.fill("キャンセルテスト")

        # 取消
        page.click("tr:has-text('U001') button.btn-ghost")
        page.wait_for_selector("tr:has-text('U001'):not(:has(input.edit-input))")

        # 元の値が表示
        assert page.locator("text=田中太郎").is_visible()
        assert not page.locator("text=キャンセルテスト").is_visible()


class TestUserCreate:
    """新規作成テスト"""

    def test_create_adds_new_row(self, page, base_url):
        """新規作成で行が追加される"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U001")

        # フォーム入力
        page.fill("input[name='cd']", "U999")
        page.fill("input[name='name']", "新規ユーザー")
        page.fill("input[name='email']", "new@example.com")

        # 追加ボタン
        page.click("form button[type='submit']")
        page.wait_for_selector("text=U999")

        # 追加確認
        assert page.locator("text=U999").is_visible()
        assert page.locator("text=新規ユーザー").is_visible()


class TestUserDelete:
    """削除テスト"""

    def test_delete_removes_row(self, page, base_url):
        """削除で行が消える"""
        page.goto(f"{base_url}/users")
        page.wait_for_selector("text=U999")

        # 編集モードに入って削除ボタンを表示
        page.click("tr:has-text('U999') button")
        page.wait_for_selector("tr:has-text('U999') button.btn-danger")

        # 削除確認ダイアログをハンドル
        page.on("dialog", lambda dialog: dialog.accept())

        # 削除実行
        page.click("tr:has-text('U999') button.btn-danger")
        page.wait_for_function("!document.body.innerText.includes('U999')")

        # 削除確認
        assert not page.locator("text=U999").is_visible()
