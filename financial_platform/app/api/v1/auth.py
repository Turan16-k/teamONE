from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.api.deps import get_current_active_user, check_rate_limit
from app.models.user import User
from app.models.log import LogAction
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
)
from app.schemas.user import (
    UserCreate, LoginRequest, TokenResponse, UserResponse,
    RefreshRequest, ChangePasswordRequest,
)
from app.utils.logging import log_audit

router = APIRouter(prefix="/auth", tags=["Auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    # Rate limit: IP başına 5 kayıt / 10 dakika
    check_rate_limit(f"register:{_client_ip(request)}", max_requests=5, window_seconds=600)

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
    )
    db.add(user)
    db.flush()
    log_audit(db, user.id, LogAction.CREATE, "User", user.id,
              ip_address=_client_ip(request))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    ip = _client_ip(request)
    # Rate limit: IP başına 10 deneme / 5 dakika
    check_rate_limit(f"login:{ip}", max_requests=10, window_seconds=300)

    user = db.query(User).filter(User.email == payload.email, User.is_active == True).first()
    # Timing attack'i önlemek için her durumda hash verify et
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    log_audit(db, user.id, LogAction.LOGIN, "User", user.id, ip_address=ip)
    db.commit()

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": user,
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    # Rate limit: IP başına 20 refresh / 5 dakika
    check_rate_limit(f"refresh:{_client_ip(request)}", max_requests=20, window_seconds=300)

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş refresh token.",
    )
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise credentials_exc
        user_id_raw = data.get("sub")
        if not user_id_raw:
            raise credentials_exc
        user_id = int(user_id_raw)
    except (JWTError, ValueError, TypeError):
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise credentials_exc

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "user": user,
    }


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    # Rate limit: kullanıcı başına 5 deneme / 10 dakika
    check_rate_limit(f"chgpw:{current_user.id}", max_requests=5, window_seconds=600)

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Yeni şifre eski şifreyle aynı olamaz.")

    current_user.hashed_password = get_password_hash(payload.new_password)
    log_audit(db, current_user.id, LogAction.UPDATE, "User", current_user.id,
              new_values={"action": "password_change"},
              ip_address=_client_ip(request))
    db.commit()
