"""
Satın alma akışı bildirim servisi.
Admin'e yeni talep, user'a onay/red bildirimi veritabanına yazılır.
"""
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.models.user import UserRole, User


def notify_admin_new_purchase(db: Session, purchase_id: int, user_full_name: str, package_name: str) -> None:
    admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active == True).all()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            type=NotificationType.PURCHASE_REQUEST,
            title="Yeni Abonelik Talebi",
            body=f"{user_full_name} kullanıcısı '{package_name}' paketi için talepte bulundu.",
            meta={"purchase_request_id": purchase_id},
        )
        db.add(notif)


def notify_user_purchase_approved(db: Session, user_id: int, package_name: str) -> None:
    notif = Notification(
        user_id=user_id,
        type=NotificationType.PURCHASE_APPROVED,
        title="Abonelik Talebiniz Onaylandı",
        body=f"'{package_name}' aboneliğiniz aktifleştirildi. İyi çalışmalar!",
    )
    db.add(notif)


def notify_user_purchase_rejected(db: Session, user_id: int, package_name: str, admin_note: str = "") -> None:
    body = f"'{package_name}' abonelik talebiniz reddedildi."
    if admin_note:
        body += f" Admin notu: {admin_note}"
    notif = Notification(
        user_id=user_id,
        type=NotificationType.PURCHASE_REJECTED,
        title="Abonelik Talebi Reddedildi",
        body=body,
    )
    db.add(notif)


def notify_user_report_ready(db: Session, user_id: int, report_id: int, company_name: str) -> None:
    notif = Notification(
        user_id=user_id,
        type=NotificationType.REPORT_READY,
        title="AI Analizi Tamamlandı",
        body=f"{company_name} için AI finansal analizi hazır.",
        meta={"report_id": report_id},
    )
    db.add(notif)
