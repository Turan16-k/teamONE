"""
FastAPI entegrasyon endpoint'i.
main.py'ye eklemek için:
    from app.services.document_analyzer.api_endpoint import router as doc_router
    app.include_router(doc_router, prefix="/api/v1")
"""
from __future__ import annotations
import zipfile
import io
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.config import settings

from .service import DocumentAnalyzerService
from .models import AnalysisTier, PACKAGE_TO_TIER

router = APIRouter(prefix="/document-analyzer", tags=["Document Analyzer"])

_svc: Optional[DocumentAnalyzerService] = None


def _get_svc() -> DocumentAnalyzerService:
    global _svc
    if _svc is None:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=503, detail="GEMINI_API_KEY henüz yapılandırılmamış.")
        _svc = DocumentAnalyzerService(api_key=settings.GEMINI_API_KEY)
    return _svc


def _resolve_tier(tier_str: str, user: User) -> AnalysisTier:
    """tier_str geçerliyse onu kullan; yoksa kullanıcının abonelik paketinden belirle."""
    if tier_str in ("basic", "professional", "enterprise"):
        return AnalysisTier(tier_str)
    sub = getattr(user, "subscription", None)
    pkg_name = sub.package.name if sub and getattr(sub, "package", None) else "Başlangıç"
    return PACKAGE_TO_TIER.get(pkg_name, AnalysisTier.BASIC)


# ── Endpoint 1: Analiz et → JSON özet dön ────────────────────────────────────

@router.post("/analyze")
async def analyze_zip(
    file: UploadFile = File(..., description="ZIP dosyası (.zip)"),
    tier: str = Form(
        "professional",
        description="Analiz seviyesi: basic | professional | enterprise",
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    ZIP dosyasındaki belgeleri AI ile analiz eder.

    - **basic** (Başlangıç): Metin özet + JSON
    - **professional** (Profesyonel): + Grafikler + PDF rapor
    - **enterprise** (Kurumsal): + PPTX sunum + Excel çalışma kitabı + kapsamlı analiz
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Yalnızca .zip uzantılı dosya kabul edilir.")

    content = await file.read()
    if len(content) > 150 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="ZIP dosyası 150 MB sınırını aşıyor.")

    # ZIP geçerlilik kontrolü
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise HTTPException(status_code=400, detail="Geçersiz ZIP dosyası.")

    tier_enum = _resolve_tier(tier, current_user)
    svc = _get_svc()

    try:
        result = svc.analyze_zip(content, tier=tier_enum)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {exc}")

    return {
        "tier": result.tier.value,
        "document_count": result.document_count,
        "total_text_chars": result.total_text_chars,
        "executive_summary": result.executive_summary,
        "key_insights": result.key_insights,
        "recommendations": result.recommendations,
        "anomalies": result.anomalies,
        "financial_metrics": (
            result.financial_metrics.model_dump() if result.financial_metrics else None
        ),
        "document_summaries": [s.model_dump() for s in result.document_summaries],
        "generated_files": list(result.report_files.keys()),
    }


# ── Endpoint 2: Analiz et + belirli dosyayı indir ────────────────────────────

@router.post("/analyze/download")
async def analyze_and_download(
    file: UploadFile = File(...),
    tier: str = Form("professional"),
    output_file: str = Form(
        "finansal_rapor.pdf",
        description="İndirilecek dosya: finansal_rapor.pdf | sunum.pptx | veri_tablosu.xlsx | analiz_sonucu.json",
    ),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    ZIP dosyasını analiz eder ve seçilen rapor dosyasını indirir.
    """
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Yalnızca .zip uzantılı dosya kabul edilir.")

    content = await file.read()
    tier_enum = _resolve_tier(tier, current_user)
    svc = _get_svc()

    try:
        result = svc.analyze_zip(content, tier=tier_enum)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analiz hatası: {exc}")

    if output_file not in result.report_files:
        raise HTTPException(
            status_code=404,
            detail=f"Dosya bulunamadı. Mevcut: {list(result.report_files.keys())}",
        )

    ext_to_mime = {
        "pdf":  "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json; charset=utf-8",
        "png":  "image/png",
    }
    ext = output_file.rsplit(".", 1)[-1].lower()
    mime = ext_to_mime.get(ext, "application/octet-stream")

    return Response(
        content=result.report_files[output_file],
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{output_file}"'},
    )
