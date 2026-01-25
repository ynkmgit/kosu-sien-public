# 工数支援システム (kosu-sien)

プロジェクト・ユーザー・案件を管理し、工数記録の基盤を提供するWebアプリケーション。

## 技術スタック

- FastAPI + HTMX + Jinja2
- SQLite
- Docker Compose

## セットアップ

```bash
# 起動
docker-compose -f infra/docker-compose.yml up -d --build

# 確認
docker-compose -f infra/docker-compose.yml logs -f

# 停止
docker-compose -f infra/docker-compose.yml down
```

URL: http://localhost:8000

## テスト

```bash
pytest tests/ -v
```

## ライセンス

MIT
