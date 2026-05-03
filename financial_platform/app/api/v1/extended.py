"""
Extended API: CompanyBank, Collection, CompanyProject, Investment + Financial Status
"""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.extended import (
    CompanyBank, Collection, CompanyProject, Investment,
    CollectionType, ProjectStatus, InvestmentStatus,
)
from app.schemas.extended import (
    BankCreate, BankUpdate, BankResponse,
    CollectionCreate, CollectionUpdate, CollectionResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    InvestmentCreate, InvestmentUpdate, InvestmentResponse,
    FinancialStatusResponse,
)
from app.utils.logging import logger

router = APIRouter(tags=["extended"])


def _get_company_or_404(company_id: int, db: Session, user: User) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Şirket bulunamadı.")
    if company.owner_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Bu şirkete erişim yetkiniz yok.")
    return company


def _safe_decimal(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0


# ── BANKS ──────────────────────────────────────────────────────────────────────

@router.get("/companies/{company_id}/banks", response_model=list[BankResponse])
def list_banks(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    return db.query(CompanyBank).filter(CompanyBank.company_id == company_id).all()


@router.post("/companies/{company_id}/banks", response_model=BankResponse, status_code=201)
def create_bank(
    company_id: int,
    body: BankCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    bank = CompanyBank(company_id=company_id, **body.model_dump())
    db.add(bank)
    db.commit()
    db.refresh(bank)
    logger.info("bank_created", company_id=company_id, bank_id=bank.id, user_id=current_user.id)
    return bank


@router.put("/companies/{company_id}/banks/{bank_id}", response_model=BankResponse)
def update_bank(
    company_id: int,
    bank_id: int,
    body: BankUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    bank = db.query(CompanyBank).filter(CompanyBank.id == bank_id, CompanyBank.company_id == company_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banka kaydı bulunamadı.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(bank, k, v)
    db.commit()
    db.refresh(bank)
    return bank


@router.delete("/companies/{company_id}/banks/{bank_id}", status_code=204)
def delete_bank(
    company_id: int,
    bank_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    bank = db.query(CompanyBank).filter(CompanyBank.id == bank_id, CompanyBank.company_id == company_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banka kaydı bulunamadı.")
    db.delete(bank)
    db.commit()


# ── COLLECTIONS ───────────────────────────────────────────────────────────────

@router.get("/companies/{company_id}/collections", response_model=list[CollectionResponse])
def list_collections(
    company_id: int,
    collection_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    q = db.query(Collection).filter(Collection.company_id == company_id)
    if collection_type:
        q = q.filter(Collection.collection_type == collection_type)
    return q.order_by(Collection.due_date.asc()).all()


@router.post("/companies/{company_id}/collections", response_model=CollectionResponse, status_code=201)
def create_collection(
    company_id: int,
    body: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    coll = Collection(company_id=company_id, **body.model_dump())
    db.add(coll)
    db.commit()
    db.refresh(coll)
    logger.info("collection_created", company_id=company_id, collection_id=coll.id, user_id=current_user.id)
    return coll


@router.put("/companies/{company_id}/collections/{coll_id}", response_model=CollectionResponse)
def update_collection(
    company_id: int,
    coll_id: int,
    body: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    coll = db.query(Collection).filter(Collection.id == coll_id, Collection.company_id == company_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Tahsilat kaydı bulunamadı.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(coll, k, v)
    db.commit()
    db.refresh(coll)
    return coll


@router.delete("/companies/{company_id}/collections/{coll_id}", status_code=204)
def delete_collection(
    company_id: int,
    coll_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    coll = db.query(Collection).filter(Collection.id == coll_id, Collection.company_id == company_id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Tahsilat kaydı bulunamadı.")
    db.delete(coll)
    db.commit()


# ── PROJECTS ──────────────────────────────────────────────────────────────────

@router.get("/companies/{company_id}/projects", response_model=list[ProjectResponse])
def list_projects(
    company_id: int,
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    q = db.query(CompanyProject).filter(CompanyProject.company_id == company_id)
    if status_filter:
        q = q.filter(CompanyProject.status == status_filter)
    return q.order_by(CompanyProject.start_date.desc()).all()


@router.post("/companies/{company_id}/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    company_id: int,
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    proj = CompanyProject(company_id=company_id, **body.model_dump())
    db.add(proj)
    db.commit()
    db.refresh(proj)
    logger.info("project_created", company_id=company_id, project_id=proj.id, user_id=current_user.id)
    return proj


@router.put("/companies/{company_id}/projects/{proj_id}", response_model=ProjectResponse)
def update_project(
    company_id: int,
    proj_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    proj = db.query(CompanyProject).filter(CompanyProject.id == proj_id, CompanyProject.company_id == company_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(proj, k, v)
    db.commit()
    db.refresh(proj)
    return proj


@router.delete("/companies/{company_id}/projects/{proj_id}", status_code=204)
def delete_project(
    company_id: int,
    proj_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    proj = db.query(CompanyProject).filter(CompanyProject.id == proj_id, CompanyProject.company_id == company_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    db.delete(proj)
    db.commit()


# ── INVESTMENTS ───────────────────────────────────────────────────────────────

@router.get("/companies/{company_id}/investments", response_model=list[InvestmentResponse])
def list_investments(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    return db.query(Investment).filter(Investment.company_id == company_id).order_by(Investment.created_at.desc()).all()


@router.post("/companies/{company_id}/investments", response_model=InvestmentResponse, status_code=201)
def create_investment(
    company_id: int,
    body: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    inv = Investment(company_id=company_id, **body.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    logger.info("investment_created", company_id=company_id, investment_id=inv.id, user_id=current_user.id)
    return inv


@router.put("/companies/{company_id}/investments/{inv_id}", response_model=InvestmentResponse)
def update_investment(
    company_id: int,
    inv_id: int,
    body: InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    inv = db.query(Investment).filter(Investment.id == inv_id, Investment.company_id == company_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Yatırım bulunamadı.")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(inv, k, v)
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/companies/{company_id}/investments/{inv_id}", status_code=204)
def delete_investment(
    company_id: int,
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)
    inv = db.query(Investment).filter(Investment.id == inv_id, Investment.company_id == company_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Yatırım bulunamadı.")
    db.delete(inv)
    db.commit()


# ── FINANCIAL STATUS SUMMARY ──────────────────────────────────────────────────

@router.get("/companies/{company_id}/financial-status", response_model=FinancialStatusResponse)
def financial_status(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_company_or_404(company_id, db, current_user)

    banks = db.query(CompanyBank).filter(CompanyBank.company_id == company_id).all()
    collections = db.query(Collection).filter(Collection.company_id == company_id).all()
    projects = db.query(CompanyProject).filter(CompanyProject.company_id == company_id).all()
    investments = db.query(Investment).filter(Investment.company_id == company_id).all()

    pending = [c for c in collections if c.collection_type == CollectionType.PENDING]
    completed = [c for c in collections if c.collection_type == CollectionType.COMPLETED]
    ongoing_projects = [p for p in projects if p.status == ProjectStatus.ONGOING]
    done_projects = [p for p in projects if p.status == ProjectStatus.COMPLETED]
    active_invs = [i for i in investments if i.status == InvestmentStatus.ACTIVE]

    return FinancialStatusResponse(
        total_pending_collections=sum(_safe_decimal(c.amount) for c in pending),
        total_completed_collections=sum(_safe_decimal(c.amount) for c in completed),
        overdue_collections_count=sum(1 for c in pending if c.is_overdue),
        total_bank_balance=sum(_safe_decimal(b.balance) for b in banks),
        total_credit_limit=sum(_safe_decimal(b.credit_limit) for b in banks),
        total_credit_usage=sum(_safe_decimal(b.credit_usage) for b in banks),
        ongoing_projects_count=len(ongoing_projects),
        completed_projects_count=len(done_projects),
        total_project_value=sum(_safe_decimal(p.value) for p in projects),
        active_investments_count=len(active_invs),
        total_investment_value=sum(_safe_decimal(i.current_value) for i in active_invs),
    )


# ── OUR COMPANIES (Firmalarımız) – danışmanlık firması görünümü ────────────────

@router.get("/our-companies/contracts")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Danışmanlık firmasına ait tüm şirketler ve sözleşme özeti."""
    companies = db.query(Company).filter(Company.owner_id == current_user.id).all()
    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "name": c.name,
            "sector": c.sector,
            "contract_type": c.contract_type,
            "contract_amount": float(c.contract_amount) if c.contract_amount else None,
            "contract_start": c.contract_start.isoformat() if c.contract_start else None,
            "contract_end": c.contract_end.isoformat() if c.contract_end else None,
            "authorized_person_name": c.authorized_person_name,
            "contact_phone": c.contact_phone,
            "contact_email": c.contact_email,
        })
    return result
