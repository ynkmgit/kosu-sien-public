"""報告テンプレートAPI

責務: HTTPルーティングのみ
データ操作はReportTemplateServiceに委譲
"""
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import ReportTemplateService

router = APIRouter(prefix="/api/report-templates", tags=["report-templates"])


class TemplateBody(BaseModel):
    name: str
    body: str
    options: dict = {}


@router.get("")
def list_templates():
    """全テンプレート取得"""
    return JSONResponse({"templates": ReportTemplateService.get_all()})


@router.post("")
def create_template(data: TemplateBody):
    """テンプレート新規作成"""
    t = ReportTemplateService.create(
        name=data.name,
        body=data.body,
        options=json.dumps(data.options),
    )
    return JSONResponse(t, status_code=201)


@router.put("/{template_id}")
def update_template(template_id: int, data: TemplateBody):
    """テンプレート更新"""
    t = ReportTemplateService.update(
        template_id=template_id,
        name=data.name,
        body=data.body,
        options=json.dumps(data.options),
    )
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return JSONResponse(t)


@router.delete("/{template_id}")
def delete_template(template_id: int):
    """テンプレート削除（最後の1件は削除不可）"""
    if not ReportTemplateService.delete(template_id):
        raise HTTPException(status_code=400, detail="最後のテンプレートは削除できません")
    return JSONResponse({"status": "ok"})
