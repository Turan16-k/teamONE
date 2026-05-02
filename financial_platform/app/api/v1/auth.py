from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.log import LogAction
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.user import UserCreate, LoginRequest, TokenResponse, UserResponse
from app.utils.logging import log_audit

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()
    log_audit(db, user.id, LogAction.CREATE, "User", user.id,
              ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email, User.is_active == True).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı.")

    log_audit(db, user.id, LogAction.LOGIN, "User", user.id,
              ip_address=request.client.host if request.client else None)
    db.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }
