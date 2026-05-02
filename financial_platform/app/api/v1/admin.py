"""
T1 & T7: Admin Panel Endpoint'leri
Satın alma onayı, kullanıcı yönetimi, log görüntüleme.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.subscription import PurchaseRequest, PurchaseStatus, UserSubscription, SubscriptionStatus
from app.models.log import AuditLog, AIOperationLog
from app.schemas.subscription import PurchaseRequestResponse, ReviewPurchaseRequest
from app.schemas.user import UserResponse, UserUpdate
from app.utils.pagination import PaginationParams, paginate, orm_to_dict
from app.services.notification_service import (
    notify_user_purchase_approved,
    notify_user_purchase_rejected,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/purchase-requests", response_model=dict)
def list_purchase_requests(
    page: int = 1,
    page_size: int = 20,
    status_filter: str = "pending",
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """T - Satın Alma Akışı: Admin'e düşen bekleyen talepler."""
    query = db.query(PurchaseRequest)
    try:
        query = query.filter(PurchaseRequest.status == PurchaseStatus(status_filter))
    except ValueError:
        pass
    result = paginate(query.order_by(PurchaseRequest.created_at.desc()),
                      PaginationParams(page=page, page_size=page_size))
    result["items"] = [PurchaseRequestResponse.model_validate(r) for r in result["items"]]
    return result


@router.post("/purchase-requests/{request_id}/review", response_model=PurchaseRequestResponse)
def review_purchase_request(
    request_id: int,
    payload: ReviewPurchaseRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> PurchaseRequest:
    """T - Satın Alma Akışı: Onayla veya reddet; onayda aboneliği aktifleştir."""
    purchase = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    if purchase.status != PurchaseStatus.PENDING:
        raise HTTPException(status_code=400, detail="Bu talep zaten işleme alınmış.")

    purchase.status = payload.status
    purchase.admin_note = payload.admin_note
    purchase.reviewed_by = current_user.id
    purchase.reviewed_at = datetime.utcnow()

    package = purchase.package

    if payload.status == PurchaseStatus.APPROVED:
        from datetime import timedelta
        existing = db.query(UserSubscription).filter(UserSubscription.user_id == purchase.user_id).first()
        now = datetime.utcnow()

        if existing:
            existing.package_id = purchase.package_id
            existing.status = SubscriptionStatus.ACTIVE
            existing.start_date = now
            existing.end_date = now + timedelta(days=package.duration_days)
            existing.ai_calls_used = 0
            existing.reports_used = 0
        else:
            subscription = UserSubscription(
                user_id=purchase.user_id,
                package_id=purchase.package_id,
                status=SubscriptionStatus.ACTIVE,
                start_date=now,
                end_date=now + timedelta(days=package.duration_days),
            )
            db.add(subscription)

        notify_user_purchase_approved(db, purchase.user_id, package.name)

    elif payload.status == PurchaseStatus.REJECTED:
        notify_user_purchase_rejected(db, purchase.user_id, package.name, payload.admin_note or "")

    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/users", response_model=dict)
def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(User).order_by(User.created_at.desc())
    result = paginate(query, PaginationParams(page=page, page_size=page_size))
    result["items"] = [UserResponse.model_validate(u) for u in result["items"]]
    return result


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> None:
    """Kullanıcıyı siler (hard delete). Kendi hesabını silemez."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Kendi hesabınızı silemezsiniz.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    db.delete(user)
    db.commit()


@router.get("/stats/platform", response_model=dict)
def get_platform_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """Genel platform metrikleri: kullanıcı, şirket, rapor, abonelik sayıları."""
    from sqlalchemy import func
    from app.models.company import Company
    from app.models.financial import FinancialReport
    from app.models.subscription import UserSubscription, SubscriptionStatus

    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    total_companies = db.query(func.count(Company.id)).scalar()
    total_reports = db.query(func.count(FinancialReport.id)).scalar()
    ai_reports = db.query(func.count(FinancialReport.id)).filter(
        FinancialReport.is_ai_generated == True
    ).scalar()
    active_subs = db.query(func.count(UserSubscription.id)).filter(
        UserSubscription.status == SubscriptionStatus.ACTIVE
    ).scalar()
    pending_purchases = db.query(func.count(PurchaseRequest.id)).filter(
        PurchaseRequest.status == PurchaseStatus.PENDING
    ).scalar()

    return {
        "users": {"total": total_users, "active": active_users},
        "companies": {"total": total_companies},
        "reports": {"total": total_reports, "ai_generated": ai_reports},
        "subscriptions": {"active": active_subs, "pending_purchases": pending_purchases},
    }


@router.get("/logs/audit", response_model=dict)
def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """T9: CRUD audit loglarını görüntüle."""
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    result = paginate(query, PaginationParams(page=page, page_size=page_size))
    result["items"] = [orm_to_dict(r) for r in result["items"]]
    return result


@router.get("/logs/ai", response_model=dict)
def get_ai_logs(
    page: int = 1,
    page_size: int = 50,
    service: str = None,
    success: bool = None,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """T9: AI/OCR işlem metriklerini görüntüle."""
    query = db.query(AIOperationLog)
    if service:
        query = query.filter(AIOperationLog.service == service)
    if success is not None:
        query = query.filter(AIOperationLog.success == success)
    query = query.order_by(AIOperationLog.created_at.desc())
    result = paginate(query, PaginationParams(page=page, page_size=page_size))
    result["items"] = [orm_to_dict(r) for r in result["items"]]
    return result


@router.get("/stats/ai", response_model=dict)
def get_ai_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> dict:
    """T9: AI metrikleri özet istatistikleri."""
    from sqlalchemy import func
    total = db.query(func.count(AIOperationLog.id)).scalar()
    success_count = db.query(func.count(AIOperationLog.id)).filter(AIOperationLog.success == True).scalar()
    avg_duration = db.query(func.avg(AIOperationLog.duration_ms)).filter(AIOperationLog.success == True).scalar()
    total_tokens = db.query(func.sum(AIOperationLog.total_tokens)).scalar()

    by_service = (
        db.query(AIOperationLog.service, func.count(AIOperationLog.id).label("count"))
        .group_by(AIOperationLog.service)
        .all()
    )

    return {
        "total_calls": total,
        "success_count": success_count,
        "error_count": (total or 0) - (success_count or 0),
        "success_rate": round((success_count / total * 100), 2) if total else 0,
        "avg_duration_ms": round(float(avg_duration), 2) if avg_duration else None,
        "total_tokens_used": total_tokens,
        "by_service": {row.service: row.count for row in by_service},
    }
