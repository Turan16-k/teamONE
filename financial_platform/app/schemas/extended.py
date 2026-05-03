from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


# ── CompanyBank ────────────────────────────────────────────────────────────────

class BankCreate(BaseModel):
    bank_name: str
    account_no: Optional[str] = None
    currency: str = "TRY"
    balance: Optional[float] = None
    credit_limit: Optional[float] = None
    credit_usage: Optional[float] = None
    notes: Optional[str] = None


class BankUpdate(BaseModel):
    bank_name: Optional[str] = None
    account_no: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[float] = None
    credit_limit: Optional[float] = None
    credit_usage: Optional[float] = None
    notes: Optional[str] = None


class BankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    bank_name: str
    account_no: Optional[str] = None
    currency: str
    balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    credit_usage: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Collection (Tahsilat) ──────────────────────────────────────────────────────

class CollectionCreate(BaseModel):
    collection_type: str
    amount: float
    description: Optional[str] = None
    counterparty: Optional[str] = None
    due_date: Optional[date] = None
    collection_date: Optional[date] = None
    is_overdue: bool = False


class CollectionUpdate(BaseModel):
    collection_type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    counterparty: Optional[str] = None
    due_date: Optional[date] = None
    collection_date: Optional[date] = None
    is_overdue: Optional[bool] = None


class CollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    collection_type: str
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    counterparty: Optional[str] = None
    due_date: Optional[date] = None
    collection_date: Optional[date] = None
    is_overdue: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── CompanyProject ─────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    status: str = "ongoing"
    client_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[float] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[float] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    status: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Investment ─────────────────────────────────────────────────────────────────

class InvestmentCreate(BaseModel):
    name: str
    investment_type: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    status: str = "active"
    purchase_value: Optional[float] = None
    current_value: Optional[float] = None
    planned_return_pct: Optional[str] = None
    risk_score: Optional[int] = None
    notes: Optional[str] = None
    purchase_date: Optional[date] = None
    exit_date: Optional[date] = None


class InvestmentUpdate(BaseModel):
    name: Optional[str] = None
    investment_type: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    status: Optional[str] = None
    purchase_value: Optional[float] = None
    current_value: Optional[float] = None
    planned_return_pct: Optional[str] = None
    risk_score: Optional[int] = None
    notes: Optional[str] = None
    purchase_date: Optional[date] = None
    exit_date: Optional[date] = None


class InvestmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    investment_type: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    status: str
    purchase_value: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    planned_return_pct: Optional[str] = None
    risk_score: Optional[int] = None
    notes: Optional[str] = None
    purchase_date: Optional[date] = None
    exit_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Financial Status Summary ───────────────────────────────────────────────────

class FinancialStatusResponse(BaseModel):
    total_pending_collections: float
    total_completed_collections: float
    overdue_collections_count: int
    total_bank_balance: float
    total_credit_limit: float
    total_credit_usage: float
    ongoing_projects_count: int
    completed_projects_count: int
    total_project_value: float
    active_investments_count: int
    total_investment_value: float
