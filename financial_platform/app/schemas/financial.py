from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from decimal import Decimal
from datetime import datetime
from app.models.financial import ReportType, PeriodType


class FinancialReportCreate(BaseModel):
    company_id: int
    report_type: ReportType
    period: PeriodType
    fiscal_year: int
    notes: Optional[str] = None

    # Balance Sheet
    cash_and_equivalents: Optional[Decimal] = None
    short_term_investments: Optional[Decimal] = None
    accounts_receivable: Optional[Decimal] = None
    inventory: Optional[Decimal] = None
    other_current_assets: Optional[Decimal] = None
    total_current_assets: Optional[Decimal] = None
    property_plant_equipment: Optional[Decimal] = None
    intangible_assets: Optional[Decimal] = None
    long_term_investments: Optional[Decimal] = None
    total_non_current_assets: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    accounts_payable: Optional[Decimal] = None
    short_term_debt: Optional[Decimal] = None
    current_portion_long_term_debt: Optional[Decimal] = None
    other_current_liabilities: Optional[Decimal] = None
    total_current_liabilities: Optional[Decimal] = None
    long_term_debt: Optional[Decimal] = None
    deferred_tax_liabilities: Optional[Decimal] = None
    total_non_current_liabilities: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    share_capital: Optional[Decimal] = None
    retained_earnings: Optional[Decimal] = None
    other_equity: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None

    # Income Statement
    revenue: Optional[Decimal] = None
    cost_of_goods_sold: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    ebit: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    income_before_tax: Optional[Decimal] = None
    income_tax: Optional[Decimal] = None
    net_income: Optional[Decimal] = None

    # Cash Flow
    operating_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None
    net_change_in_cash: Optional[Decimal] = None


class FinancialReportUpdate(BaseModel):
    """T3: Çift yönlü veri bağlama - AI doldurdu, kullanıcı düzenliyor."""
    notes: Optional[str] = None
    is_verified: Optional[bool] = None

    cash_and_equivalents: Optional[Decimal] = None
    short_term_investments: Optional[Decimal] = None
    accounts_receivable: Optional[Decimal] = None
    inventory: Optional[Decimal] = None
    other_current_assets: Optional[Decimal] = None
    total_current_assets: Optional[Decimal] = None
    property_plant_equipment: Optional[Decimal] = None
    intangible_assets: Optional[Decimal] = None
    long_term_investments: Optional[Decimal] = None
    total_non_current_assets: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None
    accounts_payable: Optional[Decimal] = None
    short_term_debt: Optional[Decimal] = None
    current_portion_long_term_debt: Optional[Decimal] = None
    other_current_liabilities: Optional[Decimal] = None
    total_current_liabilities: Optional[Decimal] = None
    long_term_debt: Optional[Decimal] = None
    deferred_tax_liabilities: Optional[Decimal] = None
    total_non_current_liabilities: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None
    share_capital: Optional[Decimal] = None
    retained_earnings: Optional[Decimal] = None
    other_equity: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None
    revenue: Optional[Decimal] = None
    cost_of_goods_sold: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    ebit: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    income_before_tax: Optional[Decimal] = None
    income_tax: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    operating_cash_flow: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    free_cash_flow: Optional[Decimal] = None
    net_change_in_cash: Optional[Decimal] = None


class FinancialReportResponse(FinancialReportCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_ai_generated: bool
    is_verified: bool
    ai_analysis: Optional[Any] = None
    ai_ratios: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime]
