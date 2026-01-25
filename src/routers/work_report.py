"""業務終了報告支援

責務: 日次工数実績をテンプレートで整形し報告書を生成
"""
from datetime import date
from html import escape

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from services import UserService, WorkLogService
from .common import templates

router = APIRouter(prefix="/work-report", tags=["work_report"])

# デフォルトテンプレート
DEFAULT_TEMPLATE = """業務終了します。
【工数実績】
 {total_hours}H
【作業実績、進捗率】
@project {project_name}
@issue {issue_cd} {issue_name}
@task   {task_name} ({progress}%)"""

WEEKDAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]


def parse_template(template: str) -> tuple[str, str, str, str]:
    """テンプレートをパースしてループ行を抽出

    責務: パースのみ

    @project, @issue, @task で始まる行を抽出し、
    残りのベーステンプレートと分離する

    Returns:
        (base_template, project_fmt, issue_fmt, task_fmt)
    """
    lines = template.split('\n')
    base_lines = []
    project_fmt = ""
    issue_fmt = ""
    task_fmt = ""
    loop_insert_index = -1

    for line in lines:
        if line.startswith('@project'):
            project_fmt = line[8:].lstrip()
            if loop_insert_index == -1:
                loop_insert_index = len(base_lines)
        elif line.startswith('@issue'):
            issue_fmt = line[6:].lstrip()
            if loop_insert_index == -1:
                loop_insert_index = len(base_lines)
        elif line.startswith('@task'):
            task_fmt = line[5:].lstrip()
            if loop_insert_index == -1:
                loop_insert_index = len(base_lines)
        else:
            base_lines.append(line)

    # ループ挿入位置に {__LOGS__} を入れる
    if loop_insert_index >= 0:
        base_lines.insert(loop_insert_index, '{__LOGS__}')

    return '\n'.join(base_lines), project_fmt, issue_fmt, task_fmt


def format_line(fmt: str, log: dict, hide_zero: bool = False) -> str:
    """1行をフォーマット

    責務: 単一行の変数展開のみ
    """
    progress = log['progress_rate'] if log['progress_rate'] is not None else 0

    result = fmt.replace(
        "{project_cd}", log['project_cd'] or ""
    ).replace(
        "{project_name}", log['project_name'] or ""
    ).replace(
        "{issue_cd}", log['issue_cd'] or ""
    ).replace(
        "{issue_name}", log['issue_name'] or ""
    ).replace(
        "{task_name}", log['task_name'] or ""
    ).replace(
        "{hours}", f"{log['hours']:.2f}"
    )

    # 0%非表示オプション
    if hide_zero and progress == 0:
        # " ({progress}%)" や " {progress}%" を除去
        result = result.replace(" ({progress}%)", "")
        result = result.replace("({progress}%)", "")
        result = result.replace(" {progress}%", "")
        result = result.replace("{progress}%", "")
        result = result.replace("{progress}", "")
    else:
        result = result.replace("{progress}", str(progress))

    return result


def format_logs(
    logs: list[dict],
    project_fmt: str,
    issue_fmt: str,
    task_fmt: str,
    hide_zero: bool = False
) -> str:
    """実績データをフォーマット

    責務: ループ処理と行結合のみ
    """
    if not logs:
        return "(実績なし)"

    lines = []
    current_project = None
    current_issue = None

    for log in logs:
        # プロジェクトが変わったら出力
        if project_fmt and log['project_name'] != current_project:
            current_project = log['project_name']
            current_issue = None
            lines.append(format_line(project_fmt, log, hide_zero))

        # 案件が変わったら出力
        if issue_fmt and log['issue_cd'] != current_issue:
            current_issue = log['issue_cd']
            lines.append(format_line(issue_fmt, log, hide_zero))

        # 作業を出力
        if task_fmt:
            lines.append(format_line(task_fmt, log, hide_zero))

    return "\n".join(lines)


def generate_report(
    template: str,
    total_hours: float,
    logs: list[dict],
    target_date: date,
    user_cd: str = "",
    user_name: str = "",
    hide_zero: bool = False
) -> str:
    """報告書を生成

    責務: 全体のオーケストレーションのみ
    """
    weekday = WEEKDAY_NAMES[target_date.weekday()]
    date_jp = f"{target_date.strftime('%Y/%m/%d')}({weekday})"

    # テンプレートをパース
    base_template, project_fmt, issue_fmt, task_fmt = parse_template(template)

    # ログをフォーマット
    logs_text = format_logs(logs, project_fmt, issue_fmt, task_fmt, hide_zero)

    return base_template.replace(
        "{total_hours}", f"{total_hours:.1f}"
    ).replace(
        "{__LOGS__}", logs_text
    ).replace(
        "{date}", target_date.strftime("%Y/%m/%d")
    ).replace(
        "{date_jp}", date_jp
    ).replace(
        "{user_cd}", user_cd
    ).replace(
        "{user_name}", user_name
    )


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    user: int = Query(default=None),
    target_date: str = Query(default=None),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    """業務終了報告ページ"""
    # デフォルトは今日
    if target_date:
        try:
            selected_date = date.fromisoformat(target_date)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    users = UserService.get_active_list()

    total_hours = 0.0
    preview = ""
    selected_user_info = None
    user_cd = ""
    user_name = ""

    if user:
        # 選択中ユーザーの情報取得
        for u in users:
            if u['id'] == user:
                selected_user_info = u
                user_cd = u['cd']
                user_name = u['name']
                break

        logs = WorkLogService.get_user_daily_logs(user, selected_date)
        total_hours = sum(log['hours'] for log in logs)
        preview = generate_report(
            DEFAULT_TEMPLATE, total_hours, logs,
            selected_date, user_cd, user_name
        )

    # グローバルフィルター用（userは単一選択なのでリストに変換）
    filter_params = {"user": [user] if user else [], "project": project, "issue": issue}
    return templates.TemplateResponse(request, "work_report.html", {
        "active": "work_report",
        "users": users,
        "selected_user": user,
        "selected_user_info": selected_user_info,
        "selected_date": selected_date.isoformat(),
        "default_template": DEFAULT_TEMPLATE,
        "total_hours": total_hours,
        "preview": preview,
        "user_cd": user_cd,
        "user_name": user_name,
        "filter_params": filter_params,
    })


@router.get("/preview", response_class=HTMLResponse)
def preview(
    user: int = Query(default=None),
    target_date: str = Query(default=None),
    template: str = Query(default=DEFAULT_TEMPLATE),
    hide_zero_progress: bool = Query(default=False)
):
    """報告書プレビューを生成（HTMX用）

    責務: HTMLフラグメント返却のみ
    """
    if not user:
        return HTMLResponse('<p class="empty-preview">ユーザーを選択してください</p>')

    # 日付パース
    try:
        selected_date = date.fromisoformat(target_date) if target_date else date.today()
    except ValueError:
        selected_date = date.today()

    users = UserService.get_active_list()
    user_cd = ""
    user_name = ""
    for u in users:
        if u['id'] == user:
            user_cd = u['cd']
            user_name = u['name']
            break

    logs = WorkLogService.get_user_daily_logs(user, selected_date)
    total_hours = sum(log['hours'] for log in logs)
    report = generate_report(
        template, total_hours, logs,
        selected_date, user_cd, user_name, hide_zero_progress
    )

    return HTMLResponse(f'<pre id="report-preview-text">{escape(report)}</pre>')
