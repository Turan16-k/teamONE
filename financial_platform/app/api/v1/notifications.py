from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.notification import Notification
from app.utils.pagination import PaginationParams, paginate, orm_to_dict

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
def list_notifications(
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    result = paginate(query.order_by(Notification.created_at.desc()),
                      PaginationParams(page=page, page_size=page_size))
    result["items"] = [orm_to_dict(n) for n in result["items"]]
    return result


@router.post("/{notification_id}/read", status_code=204)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).update({"is_read": True})
    db.commit()


@router.post("/read-all", status_code=204)
def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
