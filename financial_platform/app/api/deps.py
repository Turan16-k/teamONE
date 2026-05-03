import time
from collections import defaultdict
from threading import Lock

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()

# ── In-memory sliding-window rate limiter (thread-safe) ───────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
_rate_lock = Lock()


def check_rate_limit(key: str, max_requests: int = 10, window_seconds: int = 300) -> None:
    """429 fırlatır eğer key verilen pencerede max_requests'i aşmışsa."""
    now = time.time()
    cutoff = now - window_seconds
    with _rate_lock:
        times = _rate_store[key]
        times[:] = [t for t in times if t > cutoff]
        if len(times) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Çok fazla istek. {window_seconds // 60} dakika sonra tekrar deneyin.",
                headers={"Retry-After": str(window_seconds)},
            )
        times.append(now)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exc
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exc
        user_id = int(user_id_raw)  # ValueError burada da yakalanıyor
    except (JWTError, ValueError, TypeError):
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exc
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Hesap devre dışı.")
    return current_user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yetkiniz yok.",
        )
    return current_user


def get_request_meta(request: Request) -> dict:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }
