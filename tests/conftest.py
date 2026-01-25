"""テスト共通設定"""
import os
import pytest


@pytest.fixture(scope="session")
def base_url():
    """テスト対象のベースURL（環境変数で上書き可能）"""
    return os.getenv("TEST_BASE_URL", "http://localhost:8001")
