"""
T9: Yapılandırılmış loglama altyapısı.
- Uygulama logları: structlog ile JSON formatında
- CRUD audit logları: veritabanına yazılır
- AI metrikleri: veritabanına yazılır
- Hata yönetimi: stack trace logda, kullanıcıya clean mesaj
"""
import structlog
import logging
import traceback
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.models.log import AuditLog, AIOperationLog, LogAction

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def log_audit(
    db: Session,
    user_id: Optional[int],
    action: LogAction,
    entity_type: str,
    entity_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """CRUD işlemlerini veritabanına yaz."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        db.flush()  # ID'yi al ama commit etme (transaction içinde)
        logger.info("audit_log", action=action, entity=entity_type, entity_id=entity_id, user_id=user_id)
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))


def log_ai_operation(
    db: Session,
    user_id: Optional[int],
    service: str,
    model_used: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    request_metadata: Optional[dict] = None,
    response_metadata: Optional[dict] = None,
) -> None:
    """AI/OCR çağrı metriklerini veritabanına yaz."""
    total_tokens = None
    if prompt_tokens and completion_tokens:
        total_tokens = prompt_tokens + completion_tokens

    try:
        entry = AIOperationLog(
            user_id=user_id,
            service=service,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            success=success,
            error_type=error_type,
            error_message=error_message,
            request_metadata=request_metadata,
            response_metadata=response_metadata,
        )
        db.add(entry)
        db.flush()
        logger.info(
            "ai_operation",
            service=service,
            success=success,
            tokens=total_tokens,
            duration_ms=duration_ms,
        )
    except Exception as e:
        logger.error("ai_log_failed", error=str(e))


def log_exception(exc: Exception, context: Optional[dict] = None) -> str:
    """Stack trace'i logla, kullanıcıya dönecek temiz mesajı üret."""
    tb = traceback.format_exc()
    logger.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        exc_msg=str(exc),
        stack_trace=tb,
        context=context or {},
    )
    return "Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
