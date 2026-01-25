#!/usr/bin/env python3
"""データ投入ツール（UTF-8保証）

Windows環境でのエンコーディング問題を回避するため、
curlの代わりにこのスクリプトを使用してAPIにデータを投入する。

使用例:
    # ユーザー追加
    python scripts/data_loader.py user create --cd U001 --name "田中太郎" --email tanaka@example.com

    # ユーザー更新
    python scripts/data_loader.py user update 1 --name "田中一郎"

    # 属性タイプ追加
    python scripts/data_loader.py attr-type create --code role --name "役職"

    # 選択肢追加
    python scripts/data_loader.py option create 1 --code member --name "メンバー"

    # JSONファイルから一括投入
    python scripts/data_loader.py bulk users.json
"""
import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:8001"


def api_request(method: str, path: str, data: dict = None) -> tuple[int, str]:
    """APIリクエストを送信（UTF-8保証）

    Args:
        method: HTTP メソッド (GET, POST, PUT, DELETE)
        path: APIパス (/users など)
        data: 送信データ（辞書）

    Returns:
        (status_code, response_body)
    """
    url = f"{BASE_URL}{path}"

    encoded_data = None
    if data:
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')

    req = urllib.request.Request(url, data=encoded_data, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')


def cmd_user(args):
    """ユーザー操作"""
    if args.action == "create":
        data = {"cd": args.cd, "name": args.name, "email": args.email}
        status, body = api_request("POST", "/users", data)
        print(f"Status: {status}")
        if status == 200:
            print("ユーザーを作成しました")
        else:
            print(f"エラー: {body}")

    elif args.action == "update":
        data = {}
        if args.cd:
            data["cd"] = args.cd
        if args.name:
            data["name"] = args.name
        if args.email:
            data["email"] = args.email

        # 属性も追加可能
        for attr in (args.attrs or []):
            key, value = attr.split("=")
            data[key] = value

        status, body = api_request("PUT", f"/users/{args.id}", data)
        print(f"Status: {status}")
        if status == 200:
            print("ユーザーを更新しました")
        else:
            print(f"エラー: {body}")

    elif args.action == "delete":
        status, body = api_request("DELETE", f"/users/{args.id}")
        print(f"Status: {status}")
        if status == 200:
            print("ユーザーを削除しました")
        else:
            print(f"エラー: {body}")


def cmd_attr_type(args):
    """属性タイプ操作"""
    if args.action == "create":
        data = {
            "code": args.code,
            "name": args.name,
            "sort_order": args.sort_order or 0
        }
        status, body = api_request("POST", "/user-attribute-types", data)
        print(f"Status: {status}")
        if status == 200:
            print("属性タイプを作成しました")
        else:
            print(f"エラー: {body}")

    elif args.action == "update":
        data = {}
        if args.code:
            data["code"] = args.code
        if args.name:
            data["name"] = args.name
        if args.sort_order is not None:
            data["sort_order"] = args.sort_order

        status, body = api_request("PUT", f"/user-attribute-types/{args.id}", data)
        print(f"Status: {status}")
        if status == 200:
            print("属性タイプを更新しました")
        else:
            print(f"エラー: {body}")


def cmd_option(args):
    """選択肢操作"""
    if args.action == "create":
        data = {
            "code": args.code,
            "name": args.name,
            "sort_order": args.sort_order or 0
        }
        status, body = api_request("POST", f"/user-attribute-types/{args.type_id}/options", data)
        print(f"Status: {status}")
        if status == 200:
            print("選択肢を作成しました")
        else:
            print(f"エラー: {body}")

    elif args.action == "update":
        data = {}
        if args.code:
            data["code"] = args.code
        if args.name:
            data["name"] = args.name
        if args.sort_order is not None:
            data["sort_order"] = args.sort_order

        status, body = api_request(
            "PUT",
            f"/user-attribute-types/{args.type_id}/options/{args.id}",
            data
        )
        print(f"Status: {status}")
        if status == 200:
            print("選択肢を更新しました")
        else:
            print(f"エラー: {body}")


def cmd_bulk(args):
    """JSONファイルから一括投入

    JSONフォーマット:
    {
        "users": [
            {"cd": "U001", "name": "田中太郎", "email": "tanaka@example.com", "attrs": {"attr_1": 1}}
        ],
        "attr_types": [
            {"code": "role", "name": "役職", "sort_order": 0}
        ],
        "options": [
            {"type_id": 1, "code": "member", "name": "メンバー", "sort_order": 0}
        ]
    }
    """
    json_path = Path(args.file)
    if not json_path.exists():
        print(f"エラー: ファイルが見つかりません: {json_path}")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 属性タイプ
    for item in data.get("attr_types", []):
        status, _ = api_request("POST", "/user-attribute-types", item)
        print(f"属性タイプ '{item['name']}': {status}")

    # 選択肢
    for item in data.get("options", []):
        type_id = item.pop("type_id")
        status, _ = api_request("POST", f"/user-attribute-types/{type_id}/options", item)
        print(f"選択肢 '{item['name']}': {status}")

    # ユーザー
    for item in data.get("users", []):
        attrs = item.pop("attrs", {})
        user_data = {**item, **attrs}

        if "id" in item:
            # 更新
            user_id = user_data.pop("id")
            status, _ = api_request("PUT", f"/users/{user_id}", user_data)
        else:
            # 新規作成
            status, _ = api_request("POST", "/users", user_data)
        print(f"ユーザー '{item['name']}': {status}")


def main():
    parser = argparse.ArgumentParser(
        description="データ投入ツール（UTF-8保証）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # user コマンド
    user_parser = subparsers.add_parser("user", help="ユーザー操作")
    user_sub = user_parser.add_subparsers(dest="action", required=True)

    user_create = user_sub.add_parser("create", help="ユーザー作成")
    user_create.add_argument("--cd", required=True, help="ユーザーコード")
    user_create.add_argument("--name", required=True, help="名前")
    user_create.add_argument("--email", required=True, help="メールアドレス")

    user_update = user_sub.add_parser("update", help="ユーザー更新")
    user_update.add_argument("id", type=int, help="ユーザーID")
    user_update.add_argument("--cd", help="ユーザーコード")
    user_update.add_argument("--name", help="名前")
    user_update.add_argument("--email", help="メールアドレス")
    user_update.add_argument("--attrs", nargs="*", help="属性 (attr_1=1 形式)")

    user_delete = user_sub.add_parser("delete", help="ユーザー削除")
    user_delete.add_argument("id", type=int, help="ユーザーID")

    # attr-type コマンド
    attr_parser = subparsers.add_parser("attr-type", help="属性タイプ操作")
    attr_sub = attr_parser.add_subparsers(dest="action", required=True)

    attr_create = attr_sub.add_parser("create", help="属性タイプ作成")
    attr_create.add_argument("--code", required=True, help="コード")
    attr_create.add_argument("--name", required=True, help="名前")
    attr_create.add_argument("--sort-order", type=int, help="並び順")

    attr_update = attr_sub.add_parser("update", help="属性タイプ更新")
    attr_update.add_argument("id", type=int, help="属性タイプID")
    attr_update.add_argument("--code", help="コード")
    attr_update.add_argument("--name", help="名前")
    attr_update.add_argument("--sort-order", type=int, help="並び順")

    # option コマンド
    opt_parser = subparsers.add_parser("option", help="選択肢操作")
    opt_sub = opt_parser.add_subparsers(dest="action", required=True)

    opt_create = opt_sub.add_parser("create", help="選択肢作成")
    opt_create.add_argument("type_id", type=int, help="属性タイプID")
    opt_create.add_argument("--code", required=True, help="コード")
    opt_create.add_argument("--name", required=True, help="名前")
    opt_create.add_argument("--sort-order", type=int, help="並び順")

    opt_update = opt_sub.add_parser("update", help="選択肢更新")
    opt_update.add_argument("type_id", type=int, help="属性タイプID")
    opt_update.add_argument("id", type=int, help="選択肢ID")
    opt_update.add_argument("--code", help="コード")
    opt_update.add_argument("--name", help="名前")
    opt_update.add_argument("--sort-order", type=int, help="並び順")

    # bulk コマンド
    bulk_parser = subparsers.add_parser("bulk", help="JSONファイルから一括投入")
    bulk_parser.add_argument("file", help="JSONファイルパス")

    args = parser.parse_args()

    if args.command == "user":
        cmd_user(args)
    elif args.command == "attr-type":
        cmd_attr_type(args)
    elif args.command == "option":
        cmd_option(args)
    elif args.command == "bulk":
        cmd_bulk(args)


if __name__ == "__main__":
    main()
