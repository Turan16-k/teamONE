import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, enum.Enum):
    PURCHASE_REQUEST = "purchase_request"    # admin'e: yeni satın alma talebi
    PURCHASE_APPROVED = "purchase_approved"  # user'a: talebiniz onaylandı
    PURCHASE_REJECTED = "purchase_rejected"  # user'a: talebiniz reddedildi
    REPORT_READY = "report_ready"            # user'a: AI analizi tamamlandı
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    meta = Column(JSON, nullable=True)        # ilgili entity_id, link, vb.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )
