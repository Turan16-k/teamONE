from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_active_user
from datetime import datetime, timedelta
from app.models.user import User, UserRole
from app.models.subscription import SubscriptionPackage, PurchaseRequest, PurchaseStatus, UserSubscription, SubscriptionStatus
from app.schemas.subscription import PackageResponse, PurchaseRequestCreate, PurchaseRequestResponse
from app.services.notification_service import notify_admin_new_purchase

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/packages", response_model=list[PackageResponse])
def list_packages(db: Session = Depends(get_db)) -> list:
    return db.query(SubscriptionPackage).filter(SubscriptionPackage.is_active == True).all()


@router.post("/purchase", response_model=PurchaseRequestResponse, status_code=status.HTTP_201_CREATED)
def request_purchase(
    payload: PurchaseRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PurchaseRequest:
    """Kullanıcı abonelik talebi oluşturur; admin paneline bildirim düşer."""
    package = db.query(SubscriptionPackage).filter(
        SubscriptionPackage.id == payload.package_id,
        SubscriptionPackage.is_active == True,
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Paket bulunamadı.")

    existing_pending = db.query(PurchaseRequest).filter(
        PurchaseRequest.user_id == current_user.id,
        PurchaseRequest.status == PurchaseStatus.PENDING,
    ).first()
    if existing_pending:
        raise HTTPException(status_code=400, detail="Bekleyen bir talebiniz zaten mevcut.")

    purchase = PurchaseRequest(user_id=current_user.id, package_id=payload.package_id)

    if current_user.role == UserRole.ADMIN:
        purchase.status = PurchaseStatus.APPROVED
        
        # Create or update UserSubscription for admin
        existing_sub = db.query(UserSubscription).filter(UserSubscription.user_id == current_user.id).first()
        if existing_sub:
            existing_sub.package_id = package.id
            existing_sub.status = SubscriptionStatus.ACTIVE
            existing_sub.start_date = datetime.utcnow()
            existing_sub.end_date = datetime.utcnow() + timedelta(days=package.duration_days)
            existing_sub.ai_calls_used = 0
            existing_sub.reports_used = 0
            db.add(existing_sub)
        else:
            new_sub = UserSubscription(
                user_id=current_user.id,
                package_id=package.id,
                status=SubscriptionStatus.ACTIVE,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=package.duration_days),
                ai_calls_used=0,
                reports_used=0,
            )
            db.add(new_sub)
        db.flush() # Ensure subscription ID is available for user object refresh later
    else:
        # For non-admin users, create pending purchase request and notify admin
        db.add(purchase)
        db.flush()
        notify_admin_new_purchase(db, purchase.id, current_user.full_name, package.name)

    db.commit()
    db.refresh(purchase)
    # If the current user has a subscription (admin case), refresh the user object
    # to load the updated subscription relationship.
    if current_user.subscription:
        db.refresh(current_user)
    return purchase


@router.get("/my-subscription")
def get_my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    if not current_user.subscription:
        return {"status": "no_subscription"}
    sub = current_user.subscription
    return {
        "status": sub.status.value,
        "package": sub.package.name if sub.package else None,
        "end_date": sub.end_date,
        "ai_calls_used": sub.ai_calls_used,
        "ai_calls_limit": sub.package.max_ai_calls_per_month if sub.package else None,
        "reports_used": sub.reports_used,
        "reports_limit": sub.package.max_reports_per_month if sub.package else None,
    }
