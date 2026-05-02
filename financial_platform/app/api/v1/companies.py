from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.company import Company
from app.models.log import LogAction
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.core.rbac import require_owner_or_admin
from app.utils.logging import log_audit
from app.utils.pagination import PaginationParams, paginate

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=dict)
def list_companies(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.models.user import UserRole
    params = PaginationParams(page=page, page_size=page_size)
    query = db.query(Company)

    # Admin tümünü görür, user sadece kendisini — N+1 önleme: join yok, tek query
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Company.owner_id == current_user.id)

    return paginate(query.order_by(Company.created_at.desc()), params)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Company:
    if payload.tax_id and db.query(Company).filter(Company.tax_id == payload.tax_id).first():
        raise HTTPException(status_code=400, detail="Bu vergi numarası zaten kayıtlı.")

    company = Company(**payload.model_dump(), owner_id=current_user.id)
    db.add(company)
    db.flush()
    log_audit(db, current_user.id, LogAction.CREATE, "Company", company.id,
              new_values=payload.model_dump(),
              ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    require_owner_or_admin(company.owner_id, current_user)
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    require_owner_or_admin(company.owner_id, current_user)

    old_vals = {k: getattr(company, k) for k in payload.model_dump(exclude_none=True)}
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(company, field, value)

    log_audit(db, current_user.id, LogAction.UPDATE, "Company", company_id,
              old_values=old_vals, new_values=payload.model_dump(exclude_none=True),
              ip_address=request.client.host if request.client else None)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    require_owner_or_admin(company.owner_id, current_user)

    log_audit(db, current_user.id, LogAction.DELETE, "Company", company_id,
              old_values={"name": company.name},
              ip_address=request.client.host if request.client else None)
    db.delete(company)
    db.commit()
