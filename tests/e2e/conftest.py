"""E2Eテスト用設定"""
import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser():
    """Playwrightブラウザ（セッション共有）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser, base_url):
    """新しいページ（テストごと）"""
    page = browser.new_page()
    yield page
    page.close()
