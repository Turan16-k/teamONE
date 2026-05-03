import re
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Şifre en az 8 karakter olmalıdır.")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Şifre en az bir büyük harf içermelidir.")
    if not re.search(r"[0-9]", v):
        raise ValueError("Şifre en az bir rakam içermelidir.")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("Şifre en az bir özel karakter içermelidir (!@#$%^ vb.).")
    return v


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Ad soyad en az 2 karakter olmalıdır.")
        if len(v) > 150:
            raise ValueError("Ad soyad 150 karakteri geçemez.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)
