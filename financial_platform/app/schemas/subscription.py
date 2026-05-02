from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
from app.models.subscription import SubscriptionStatus, PurchaseStatus


class PackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    price: float
    duration_days: int
    max_companies: int
    max_reports_per_month: int
    max_ai_calls_per_month: int
    features: Optional[Any]
    is_active: bool


class PurchaseRequestCreate(BaseModel):
    package_id: int


class PurchaseRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    package_id: int
    status: PurchaseStatus
    admin_note: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class ReviewPurchaseRequest(BaseModel):
    status: PurchaseStatus  # approved veya rejected
    admin_note: Optional[str] = None
