"""エンコーディング検証ミドルウェア

Windows環境のcurlで発生するMojibake（文字化け）を検出し、
不正なデータがDBに入ることを防止する。

検出パターン:
- CP932(SHIFT_JIS) → Latin-1解釈 → UTF-8保存 のダブルエンコード
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import parse_qs


def detect_mojibake(text: str) -> bool:
    """Latin-1経由のダブルエンコード（Mojibake）を検出

    Args:
        text: 検証する文字列

    Returns:
        True: 文字化けパターンを検出
        False: 正常なUTF-8テキスト
    """
    if not text:
        return False

    # ASCII文字のみなら問題なし
    if text.isascii():
        return False

    try:
        # Mojibakeの逆変換を試みる
        # UTF-8文字列 → Latin-1バイト列 → SHIFT_JIS文字列
        recovered = text.encode('latin-1').decode('shift_jis')
        # 逆変換が成功し、かつ元と違う文字列になれば文字化け
        return recovered != text
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 変換失敗 = 正常なUTF-8（または別の問題）
        return False


class EncodingValidationMiddleware(BaseHTTPMiddleware):
    """POST/PUTリクエストのフォームデータを検証するミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")

            if "application/x-www-form-urlencoded" in content_type:
                # フォームデータを読み取り
                body = await request.body()

                try:
                    # UTF-8としてデコード
                    body_str = body.decode('utf-8')
                    params = parse_qs(body_str, keep_blank_values=True)

                    # 各値をチェック
                    for key, values in params.items():
                        for value in values:
                            if detect_mojibake(value):
                                return JSONResponse(
                                    status_code=400,
                                    content={"detail": f"エンコーディングエラー: フィールド '{key}' に不正な文字が含まれています。UTF-8でデータを送信してください。"}
                                )
                except UnicodeDecodeError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "エンコーディングエラー: リクエストボディをUTF-8としてデコードできません。"}
                    )

                # bodyを再設定（FastAPIが再度読めるように）
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive

        return await call_next(request)
