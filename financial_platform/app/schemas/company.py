from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class CompanyCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    trade_registry_no: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    founding_date: Optional[date] = None
    authorized_person_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    annual_revenue_estimate: Optional[float] = None
    annual_revenue_actual: Optional[float] = None
    contract_amount: Optional[float] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    contract_type: Optional[str] = None
    parent_company_id: Optional[int] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    trade_registry_no: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    founding_date: Optional[date] = None
    authorized_person_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    annual_revenue_estimate: Optional[float] = None
    annual_revenue_actual: Optional[float] = None
    contract_amount: Optional[float] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    contract_type: Optional[str] = None
    parent_company_id: Optional[int] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tax_id: Optional[str] = None
    trade_registry_no: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    founding_date: Optional[date] = None
    authorized_person_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    annual_revenue_estimate: Optional[Decimal] = None
    annual_revenue_actual: Optional[Decimal] = None
    contract_amount: Optional[Decimal] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    contract_type: Optional[str] = None
    parent_company_id: Optional[int] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
