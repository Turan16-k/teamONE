import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class PurchaseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SubscriptionPackage(Base):
    __tablename__ = "subscription_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False, default=30)
    max_companies = Column(Integer, nullable=False, default=5)
    max_reports_per_month = Column(Integer, nullable=False, default=10)
    max_ai_calls_per_month = Column(Integer, nullable=False, default=50)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriptions = relationship("UserSubscription", back_populates="package")
    purchase_requests = relationship("PurchaseRequest", back_populates="package")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    package_id = Column(Integer, ForeignKey("subscription_packages.id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    ai_calls_used = Column(Integer, default=0, nullable=False)
    reports_used = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
    package = relationship("SubscriptionPackage", back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_user_status", "user_id", "status"),
        Index("ix_subscriptions_end_date", "end_date"),
    )


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    package_id = Column(Integer, ForeignKey("subscription_packages.id"), nullable=False)
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING, nullable=False)
    admin_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="purchase_requests", foreign_keys=[user_id])
    package = relationship("SubscriptionPackage", back_populates="purchase_requests")

    __table_args__ = (
        Index("ix_purchase_status_created", "status", "created_at"),
        Index("ix_purchase_user_status", "user_id", "status"),
    )
