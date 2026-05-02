import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean, JSON, Float, Index
from sqlalchemy.orm import relationship
from app.database import Base


class LogAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    UPLOAD = "upload"


class AuditLog(Base):
    """T9: CRUD işlemlerinin tam izlenebilirlik kaydı"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(Enum(LogAction), nullable=False)
    entity_type = Column(String(100), nullable=False)   # "FinancialReport", "Company", etc.
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)             # değişmeden önceki değerler
    new_values = Column(JSON, nullable=True)             # değişimden sonraki değerler
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_action_timestamp", "action", "timestamp"),
    )


class AIOperationLog(Base):
    """T9: LLM ve OCR çağrılarının teknik metrikleri"""
    __tablename__ = "ai_operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    service = Column(String(50), nullable=False)         # "ocr", "financial_analysis", "ratio_calc"
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=True)           # yanıt süresi (ms)
    success = Column(Boolean, default=True, nullable=False)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    request_metadata = Column(JSON, nullable=True)       # dosya adı, rapor tipi, vb.
    response_metadata = Column(JSON, nullable=True)      # güven skoru, parse edilen alan sayısı, vb.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ai_log_service_date", "service", "created_at"),
        Index("ix_ai_log_success_date", "success", "created_at"),
        Index("ix_ai_log_user_date", "user_id", "created_at"),
    )
