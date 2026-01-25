"""業務終了報告APIテスト"""
import re
import uuid
from datetime import date
import pytest

from routers.work_report import (
    parse_template,
    format_line,
    format_logs,
    generate_report,
    DEFAULT_TEMPLATE,
)


class TestParseTemplate:
    """テンプレートパースの単体テスト"""

    def test_parse_default_template(self):
        """デフォルトテンプレートがパースできる"""
        base, project_fmt, issue_fmt, task_fmt = parse_template(DEFAULT_TEMPLATE)

        assert "{__LOGS__}" in base
        assert "{project_name}" in project_fmt
        assert "{issue_cd}" in issue_fmt
        assert "{task_name}" in task_fmt

    def test_parse_no_loop_lines(self):
        """ループ行がないテンプレート"""
        template = "報告します\n{total_hours}H"
        base, project_fmt, issue_fmt, task_fmt = parse_template(template)

        assert base == "報告します\n{total_hours}H"
        assert project_fmt == ""
        assert issue_fmt == ""
        assert task_fmt == ""

    def test_parse_only_task(self):
        """@taskのみのテンプレート"""
        template = "報告\n@task {task_name}"
        base, project_fmt, issue_fmt, task_fmt = parse_template(template)

        assert "{__LOGS__}" in base
        assert project_fmt == ""
        assert issue_fmt == ""
        assert task_fmt == "{task_name}"


class TestFormatLine:
    """1行フォーマットの単体テスト"""

    def test_format_basic(self):
        """基本的な変数展開"""
        log = {
            'project_cd': 'P001',
            'project_name': 'テストPJ',
            'issue_cd': 'I001',
            'issue_name': 'テスト案件',
            'task_name': 'テスト作業',
            'progress_rate': 50,
            'hours': 2.5,
        }
        result = format_line("{task_name} ({progress}%)", log)
        assert result == "テスト作業 (50%)"

    def test_format_null_progress(self):
        """進捗率がNullの場合は0扱い"""
        log = {
            'project_cd': 'P001',
            'project_name': 'テストPJ',
            'issue_cd': 'I001',
            'issue_name': 'テスト案件',
            'task_name': 'テスト作業',
            'progress_rate': None,
            'hours': 1.0,
        }
        result = format_line("{task_name} ({progress}%)", log)
        assert result == "テスト作業 (0%)"

    def test_format_hide_zero_progress(self):
        """0%非表示オプション"""
        log = {
            'project_cd': 'P001',
            'project_name': 'テストPJ',
            'issue_cd': 'I001',
            'issue_name': 'テスト案件',
            'task_name': 'テスト作業',
            'progress_rate': 0,
            'hours': 1.0,
        }
        result = format_line("{task_name} ({progress}%)", log, hide_zero=True)
        assert result == "テスト作業"

    def test_format_hide_zero_with_nonzero(self):
        """0%以外はhide_zeroが効かない"""
        log = {
            'project_cd': 'P001',
            'project_name': 'テストPJ',
            'issue_cd': 'I001',
            'issue_name': 'テスト案件',
            'task_name': 'テスト作業',
            'progress_rate': 30,
            'hours': 1.0,
        }
        result = format_line("{task_name} ({progress}%)", log, hide_zero=True)
        assert result == "テスト作業 (30%)"


class TestFormatLogs:
    """実績フォーマットの単体テスト"""

    def test_format_empty_logs(self):
        """空の実績"""
        result = format_logs([], "", "", "")
        assert result == "(実績なし)"

    def test_format_single_log(self):
        """単一の実績"""
        logs = [{
            'project_cd': 'P001',
            'project_name': 'テストPJ',
            'issue_cd': 'I001',
            'issue_name': 'テスト案件',
            'task_name': 'テスト作業',
            'progress_rate': 50,
            'hours': 2.0,
        }]
        result = format_logs(logs, "{project_name}", "{issue_cd}", "{task_name}")
        assert "テストPJ" in result
        assert "I001" in result
        assert "テスト作業" in result

    def test_format_multiple_projects(self):
        """複数プロジェクト"""
        logs = [
            {
                'project_cd': 'P001', 'project_name': 'PJ1',
                'issue_cd': 'I001', 'issue_name': '案件1',
                'task_name': '作業1', 'progress_rate': 50, 'hours': 1.0,
            },
            {
                'project_cd': 'P002', 'project_name': 'PJ2',
                'issue_cd': 'I002', 'issue_name': '案件2',
                'task_name': '作業2', 'progress_rate': 100, 'hours': 2.0,
            },
        ]
        result = format_logs(logs, "{project_name}", "", "{task_name}")

        # プロジェクトヘッダーが2回出力される
        assert result.count("PJ1") == 1
        assert result.count("PJ2") == 1


class TestGenerateReport:
    """報告書生成の単体テスト"""

    def test_generate_basic(self):
        """基本的な報告書生成"""
        logs = [{
            'project_cd': 'P001', 'project_name': 'テストPJ',
            'issue_cd': 'I001', 'issue_name': 'テスト案件',
            'task_name': 'テスト作業', 'progress_rate': 50, 'hours': 2.0,
        }]
        result = generate_report(
            DEFAULT_TEMPLATE,
            total_hours=2.0,
            logs=logs,
            target_date=date(2026, 1, 23),
            user_cd="U001",
            user_name="テストユーザー"
        )

        assert "2.0H" in result
        assert "テストPJ" in result
        assert "テスト作業" in result

    def test_generate_with_date_vars(self):
        """日付変数の展開"""
        template = "{date} {date_jp}"
        result = generate_report(
            template,
            total_hours=0,
            logs=[],
            target_date=date(2026, 1, 23),
        )

        assert "2026/01/23" in result
        # 木曜日（曜日が括弧付きで含まれていることを確認）
        assert "(" in result and ")" in result


class TestWorkReportPage:
    """ページ表示テスト"""

    def test_page_returns_200(self, client):
        """ページ表示が成功する"""
        response = client.get("/work-report")
        assert response.status_code == 200
        assert "業務終了報告" in response.text

    def test_page_with_date_param(self, client):
        """日付指定でページ表示"""
        response = client.get("/work-report?target_date=2026-01-23")
        assert response.status_code == 200

    def test_page_with_invalid_date(self, client):
        """不正な日付でも200（今日にフォールバック）"""
        response = client.get("/work-report?target_date=invalid")
        assert response.status_code == 200


class TestWorkReportPreview:
    """プレビュー生成テスト"""

    def test_preview_without_user(self, client):
        """ユーザー未選択時のプレビュー"""
        response = client.get("/work-report/preview")
        assert response.status_code == 200
        assert "ユーザーを選択" in response.text

    def test_preview_with_user(self, client):
        """ユーザー選択時のプレビュー"""
        # テストユーザー作成
        unique_cd = f"WR-{uuid.uuid4().hex[:6]}"
        user_response = client.post("/users", data={
            "cd": unique_cd,
            "name": "報告テストユーザー",
            "email": f"{unique_cd}@test.example.com"
        })
        match = re.search(r'id="user-(\d+)"', user_response.text)
        user_id = int(match.group(1))

        response = client.get(f"/work-report/preview?user={user_id}&target_date=2026-01-23")
        assert response.status_code == 200
        assert "report-preview-text" in response.text

    def test_preview_with_custom_template(self, client):
        """カスタムテンプレートでのプレビュー"""
        unique_cd = f"WR-{uuid.uuid4().hex[:6]}"
        user_response = client.post("/users", data={
            "cd": unique_cd,
            "name": "報告テストユーザー2",
            "email": f"{unique_cd}@test.example.com"
        })
        match = re.search(r'id="user-(\d+)"', user_response.text)
        user_id = int(match.group(1))

        response = client.get(
            f"/work-report/preview?user={user_id}&target_date=2026-01-23"
            f"&template=カスタム%20{{total_hours}}H"
        )
        assert response.status_code == 200


class TestNavigationLink:
    """ナビゲーションリンクテスト"""

    def test_base_has_work_report_link(self, client):
        """ベーステンプレートに業務終了報告リンクがある"""
        response = client.get("/")
        assert response.status_code == 200
        assert "/work-report" in response.text
        assert "業務終了報告" in response.text
