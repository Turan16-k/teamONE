"""
T3 + T10: Finansal rapor CRUD endpoint'leri.
- OCR/AI pipeline: POST /documents/upload ile belge yükleme
- Manuel düzenleme: PUT ile çift yönlü veri bağlama
- N+1 önleme: joinedload ile company bilgisi tek sorguda
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import io

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.company import Company
from app.models.financial import FinancialReport, ReportType, PeriodType
from app.models.log import LogAction
from app.schemas.financial import FinancialReportCreate, FinancialReportUpdate, FinancialReportResponse
from app.core.rbac import require_owner_or_admin
from app.services.ai_service import ai_service
from app.services.pptx_service import pptx_service
from app.services.notification_service import notify_user_report_ready
from app.utils.logging import log_audit, log_exception
from app.utils.pagination import PaginationParams, paginate
from app.models.subscription import UserSubscription, SubscriptionStatus


def _check_and_increment_ai_quota(user: User, db: Session) -> None:
    """Kullanıcının AI çağrı kotasını kontrol eder; yeterliyse sayacı artırır."""
    sub: Optional[UserSubscription] = user.subscription
    if not sub or sub.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=402,
            detail="Aktif bir aboneliğiniz yok. Lütfen bir paket satın alın.",
        )
    pkg = sub.package
    if pkg and sub.ai_calls_used >= pkg.max_ai_calls_per_month:
        raise HTTPException(
            status_code=429,
            detail=f"Aylık AI çağrı limitine ulaştınız ({pkg.max_ai_calls_per_month} çağrı).",
        )
    sub.ai_calls_used += 1
    db.flush()

router = APIRouter(prefix="/financial", tags=["Financial Reports"])

ALLOWED_MEDIA_TYPES = {
    "application/pdf": "application/pdf",
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
}


def _get_company_or_403(company_id: int, current_user: User, db: Session) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    require_owner_or_admin(company.owner_id, current_user)
    return company


@router.get("/companies/{company_id}/reports", response_model=dict)
def list_reports(
    company_id: int,
    page: int = 1,
    page_size: int = 20,
    fiscal_year: Optional[int] = Query(None),
    report_type: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    _get_company_or_403(company_id, current_user, db)
    query = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.company_id == company_id)
    )
    if fiscal_year:
        query = query.filter(FinancialReport.fiscal_year == fiscal_year)
    if report_type:
        try:
            query = query.filter(FinancialReport.report_type == ReportType(report_type))
        except ValueError:
            pass
    if period:
        try:
            query = query.filter(FinancialReport.period == PeriodType(period))
        except ValueError:
            pass
    query = query.order_by(FinancialReport.fiscal_year.desc(), FinancialReport.created_at.desc())
    result = paginate(query, PaginationParams(page=page, page_size=page_size))
    result["items"] = [FinancialReportResponse.model_validate(r) for r in result["items"]]
    return result


@router.post("/companies/{company_id}/reports",
             response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    company_id: int,
    payload: FinancialReportCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FinancialReport:
    _get_company_or_403(company_id, current_user, db)
    payload.company_id = company_id

    report = FinancialReport(**payload.model_dump())
    db.add(report)
    db.flush()
    log_audit(db, current_user.id, LogAction.CREATE, "FinancialReport", report.id,
              new_values={"company_id": company_id, "fiscal_year": payload.fiscal_year,
                          "report_type": payload.report_type.value},
              ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}", response_model=FinancialReportResponse)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FinancialReport:
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)
    return report


@router.put("/reports/{report_id}", response_model=FinancialReportResponse)
def update_report(
    report_id: int,
    payload: FinancialReportUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> FinancialReport:
    """T3: Çift yönlü veri bağlama - AI doldurdu, kullanıcı manuel düzeltiyor."""
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)

    changed = payload.model_dump(exclude_none=True)
    old_vals = {k: str(getattr(report, k)) for k in changed if getattr(report, k) is not None}

    for field, value in changed.items():
        setattr(report, field, value)

    log_audit(db, current_user.id, LogAction.UPDATE, "FinancialReport", report_id,
              old_values=old_vals, new_values={k: str(v) for k, v in changed.items()},
              ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports/{report_id}/analyze", response_model=dict)
def trigger_ai_analysis(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """T3: Analitik Modül - LLM ile finansal rasyo ve değerlendirme üretir."""
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)

    financial_data = {
        "balance_sheet": {
            "total_current_assets": str(report.total_current_assets) if report.total_current_assets else None,
            "total_non_current_assets": str(report.total_non_current_assets) if report.total_non_current_assets else None,
            "total_assets": str(report.total_assets) if report.total_assets else None,
            "total_current_liabilities": str(report.total_current_liabilities) if report.total_current_liabilities else None,
            "total_non_current_liabilities": str(report.total_non_current_liabilities) if report.total_non_current_liabilities else None,
            "total_liabilities": str(report.total_liabilities) if report.total_liabilities else None,
            "total_equity": str(report.total_equity) if report.total_equity else None,
            "inventory": str(report.inventory) if report.inventory else None,
            "cash_and_equivalents": str(report.cash_and_equivalents) if report.cash_and_equivalents else None,
        },
        "income_statement": {
            "revenue": str(report.revenue) if report.revenue else None,
            "gross_profit": str(report.gross_profit) if report.gross_profit else None,
            "ebitda": str(report.ebitda) if report.ebitda else None,
            "ebit": str(report.ebit) if report.ebit else None,
            "interest_expense": str(report.interest_expense) if report.interest_expense else None,
            "net_income": str(report.net_income) if report.net_income else None,
        },
        "cash_flow": {
            "operating_cash_flow": str(report.operating_cash_flow) if report.operating_cash_flow else None,
            "free_cash_flow": str(report.free_cash_flow) if report.free_cash_flow else None,
        },
        "extra_info": {
            "banks_data": report.banks_data,
            "collections_data": report.collections_data,
            "debts_credits_data": report.debts_credits_data,
            "projects_data": report.projects_data,
            "activity_conditions": report.activity_conditions,
        }
    }

    _check_and_increment_ai_quota(current_user, db)

    try:
        analysis = ai_service.analyze_financial_ratios(financial_data, db, current_user.id)
        report.ai_ratios = analysis
        report.is_ai_generated = True
        notify_user_report_ready(db, current_user.id, report_id, report.company.name)
        db.commit()
        return {"status": "success", "analysis": analysis}
    except Exception as exc:
        user_msg = log_exception(exc, {"report_id": report_id, "user_id": current_user.id})
        raise HTTPException(status_code=500, detail=user_msg)


@router.post("/companies/{company_id}/upload-document", response_model=dict)
async def upload_and_extract(
    company_id: int,
    request: Request,
    file: UploadFile = File(...),
    fiscal_year: int = Form(...),
    period: str = Form("annual"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """T3: OCR Pipeline - PDF/görsel yükle, AI ile parse et, forma doldur."""
    _get_company_or_403(company_id, current_user, db)

    media_type = file.content_type
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen dosya tipi: {media_type}")

    if file.size and file.size > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="Dosya boyutu 20 MB'ı aşamaz.")

    content = await file.read()
    log_audit(db, current_user.id, LogAction.UPLOAD, "Document", company_id,
              new_values={"file_name": file.filename, "size": len(content)},
              ip_address=request.client.host if request.client else None)

    _check_and_increment_ai_quota(current_user, db)

    try:
        extracted = ai_service.extract_financial_data_from_document(
            file_path=file.filename,
            file_content=content,
            media_type=ALLOWED_MEDIA_TYPES[media_type],
            db=db,
            user_id=current_user.id,
        )

        # Çıkarılan veriyi FinancialReport olarak kaydet
        period_val = extracted.get("period", period)
        report_type_val = extracted.get("report_type", "combined")

        try:
            period_enum = PeriodType(period_val)
        except ValueError:
            period_enum = PeriodType.ANNUAL

        try:
            report_type_enum = ReportType(report_type_val)
        except ValueError:
            report_type_enum = ReportType.COMBINED

        bs = extracted.get("balance_sheet", {})
        inc = extracted.get("income_statement", {})
        cf = extracted.get("cash_flow", {})

        report = FinancialReport(
            company_id=company_id,
            report_type=report_type_enum,
            period=period_enum,
            fiscal_year=extracted.get("fiscal_year", fiscal_year),
            source_document=file.filename,
            is_ai_generated=True,
            **{k: v for k, v in bs.items() if v is not None},
            **{k: v for k, v in inc.items() if v is not None},
            **{k: v for k, v in cf.items() if v is not None},
        )
        db.add(report)
        db.flush()

        log_audit(db, current_user.id, LogAction.CREATE, "FinancialReport", report.id,
                  new_values={"source": "ai_ocr", "file": file.filename},
                  ip_address=request.client.host if request.client else None)
        db.commit()
        db.refresh(report)

        return {
            "status": "success",
            "report_id": report.id,
            "confidence_score": extracted.get("confidence_score"),
            "notes": extracted.get("notes"),
            "extracted_data": extracted,
        }

    except Exception as exc:
        user_msg = log_exception(exc, {"company_id": company_id, "file": file.filename})
        raise HTTPException(status_code=500, detail=user_msg)


@router.get("/reports/{report_id}/export/pptx")
def export_pptx(
    report_id: int,
    currency: str = "TRY",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """T5: Finansal raporu .pptx formatında indir."""
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)

    log_audit(db, current_user.id, LogAction.EXPORT, "FinancialReport", report_id,
              new_values={"format": "pptx"})
    db.commit()

    pptx_bytes = pptx_service.generate_financial_report(
        company=report.company,
        report=report,
        ai_analysis=report.ai_ratios,
        currency=currency,
    )

    filename = f"{report.company.name}_{report.fiscal_year}_{report.period.value}.pptx"
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)

    log_audit(db, current_user.id, LogAction.DELETE, "FinancialReport", report_id,
              old_values={"company_id": report.company_id, "fiscal_year": report.fiscal_year},
              ip_address=request.client.host if request.client else None)
    db.delete(report)
    db.commit()


@router.get("/companies/{company_id}/reports/compare", response_model=dict)
def compare_years(
    company_id: int,
    year_a: int = Query(..., description="Karşılaştırılacak birinci yıl"),
    year_b: int = Query(..., description="Karşılaştırılacak ikinci yıl"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """İki farklı mali yılın temel kalemlerini yan yana karşılaştırır."""
    _get_company_or_403(company_id, current_user, db)

    def _get_report(year: int) -> Optional[FinancialReport]:
        return (
            db.query(FinancialReport)
            .filter(
                FinancialReport.company_id == company_id,
                FinancialReport.fiscal_year == year,
                FinancialReport.period == PeriodType.ANNUAL,
            )
            .order_by(FinancialReport.created_at.desc())
            .first()
        )

    rep_a = _get_report(year_a)
    rep_b = _get_report(year_b)

    def _snap(r: Optional[FinancialReport]) -> Optional[dict]:
        if not r:
            return None
        return {
            "report_id": r.id,
            "total_assets": float(r.total_assets) if r.total_assets else None,
            "total_liabilities": float(r.total_liabilities) if r.total_liabilities else None,
            "total_equity": float(r.total_equity) if r.total_equity else None,
            "revenue": float(r.revenue) if r.revenue else None,
            "gross_profit": float(r.gross_profit) if r.gross_profit else None,
            "net_income": float(r.net_income) if r.net_income else None,
            "ebitda": float(r.ebitda) if r.ebitda else None,
            "operating_cash_flow": float(r.operating_cash_flow) if r.operating_cash_flow else None,
            "financial_score": r.ai_ratios.get("financial_score") if r.ai_ratios else None,
        }

    snap_a = _snap(rep_a)
    snap_b = _snap(rep_b)

    def _delta(a_val, b_val):
        if a_val is None or b_val is None or b_val == 0:
            return None
        return round((a_val - b_val) / abs(b_val) * 100, 2)

    deltas = {}
    if snap_a and snap_b:
        for key in ("total_assets", "total_liabilities", "total_equity",
                    "revenue", "gross_profit", "net_income", "ebitda", "operating_cash_flow"):
            deltas[key] = _delta(snap_a.get(key), snap_b.get(key))

    return {
        str(year_a): snap_a,
        str(year_b): snap_b,
        "change_pct": deltas,
    }


import csv

@router.get("/reports/{report_id}/export/csv")
def export_csv(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """O6: Finansal raporu CSV formatında indir."""
    report = (
        db.query(FinancialReport)
        .options(joinedload(FinancialReport.company))
        .filter(FinancialReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    require_owner_or_admin(report.company.owner_id, current_user)

    log_audit(db, current_user.id, LogAction.EXPORT, "FinancialReport", report_id,
              new_values={"format": "csv"})
    db.commit()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Başlıklar
    writer.writerow(["Firma", "Yıl", "Dönem", "Rapor Türü", "Toplam Varlık", "Toplam Yükümlülük", "Toplam Özkaynak", "Gelir", "Net Kar"])
    
    # Veriler
    writer.writerow([
        report.company.name,
        report.fiscal_year,
        report.period.value,
        report.report_type.value,
        report.total_assets,
        report.total_liabilities,
        report.total_equity,
        report.revenue,
        report.net_income
    ])

    output.seek(0)
    filename = f"{report.company.name}_{report.fiscal_year}_{report.period.value}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

