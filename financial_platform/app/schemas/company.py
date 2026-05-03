from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    commercial_register_number: Optional[str] = None
    establishment_date: Optional[datetime] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    authorized_person_name: Optional[str] = None
    contact_info: Optional[str] = None
    address: Optional[str] = None
    annual_turnover_estimate: Optional[float] = None
    contract_value: Optional[float] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    contract_type: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    commercial_register_number: Optional[str] = None
    establishment_date: Optional[datetime] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    authorized_person_name: Optional[str] = None
    contact_info: Optional[str] = None
    address: Optional[str] = None
    annual_turnover_estimate: Optional[float] = None
    contract_value: Optional[float] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    contract_type: Optional[str] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tax_id: Optional[str]
    commercial_register_number: Optional[str]
    establishment_date: Optional[datetime]
    sector: Optional[str]
    description: Optional[str]
    authorized_person_name: Optional[str]
    contact_info: Optional[str]
    address: Optional[str]
    annual_turnover_estimate: Optional[float]
    contract_value: Optional[float]
    contract_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    contract_type: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
