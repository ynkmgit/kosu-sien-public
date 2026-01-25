"""エンコーディングミドルウェアのテスト"""
import pytest
from middleware.encoding import detect_mojibake


class TestDetectMojibake:
    """detect_mojibake関数のテスト"""

    def test_ascii_text_is_safe(self):
        """ASCII文字のみは問題なし"""
        assert detect_mojibake("hello world") is False
        assert detect_mojibake("user@example.com") is False
        assert detect_mojibake("12345") is False

    def test_empty_string_is_safe(self):
        """空文字列は問題なし"""
        assert detect_mojibake("") is False
        assert detect_mojibake(None) is False

    def test_valid_utf8_japanese_is_safe(self):
        """正しいUTF-8の日本語は問題なし"""
        assert detect_mojibake("田中太郎") is False
        assert detect_mojibake("社員") is False
        assert detect_mojibake("稼働中") is False
        assert detect_mojibake("メンバー") is False

    def test_detects_mojibake_pattern(self):
        """Mojibakeパターンを検出する"""
        # "田中太郎" をSHIFT_JISでエンコードし、Latin-1→UTF-8で変換した文字列
        original = "田中太郎"
        # SHIFT_JIS bytes: 93 63 92 86 91 be 98 59
        # これをLatin-1として解釈しUTF-8エンコードしたもの
        mojibake = original.encode('shift_jis').decode('latin-1')

        assert detect_mojibake(mojibake) is True

    def test_detects_various_mojibake_patterns(self):
        """様々な日本語のMojibakeパターンを検出"""
        test_cases = ["社員", "BP", "稼働中", "待機中", "離脱", "メンバー", "リーダー", "PM"]

        for text in test_cases:
            try:
                mojibake = text.encode('shift_jis').decode('latin-1')
                # SHIFT_JISでエンコード可能な文字のみテスト
                result = detect_mojibake(mojibake)
                # mojibakeが元のtextと異なる場合、検出されるべき
                if mojibake != text:
                    assert result is True, f"Failed to detect mojibake for: {text}"
            except (UnicodeDecodeError, UnicodeEncodeError):
                # エンコードできない文字はスキップ
                pass


class TestEncodingMiddleware:
    """ミドルウェアの統合テスト"""

    def test_valid_utf8_post_succeeds(self, client):
        """正しいUTF-8でのPOSTは成功する"""
        response = client.post("/users", data={
            "cd": "TEST01",
            "name": "テスト太郎",
            "email": "test@example.com"
        })
        assert response.status_code == 200
        assert "テスト太郎" in response.text

    def test_mojibake_post_is_rejected(self, client):
        """Mojibakeを含むPOSTは拒否される"""
        # "テスト太郎" をMojibake化
        original = "テスト太郎"
        try:
            mojibake_name = original.encode('shift_jis').decode('latin-1')
        except (UnicodeDecodeError, UnicodeEncodeError):
            pytest.skip("Cannot create mojibake for this text")

        # 直接バイト列を送信（ミドルウェアをテスト）
        response = client.post(
            "/users",
            content=f"cd=TEST02&name={mojibake_name}&email=test@example.com".encode('utf-8'),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # 400エラーを期待（ミドルウェアが検出・拒否）
        assert response.status_code == 400
        assert "エンコーディングエラー" in response.text

    def test_ascii_only_post_succeeds(self, client):
        """ASCII文字のみのPOSTは成功する"""
        response = client.post("/users", data={
            "cd": "ASCII01",
            "name": "John Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 200
