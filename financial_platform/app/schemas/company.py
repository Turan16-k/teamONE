from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tax_id: Optional[str]
    sector: Optional[str]
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
