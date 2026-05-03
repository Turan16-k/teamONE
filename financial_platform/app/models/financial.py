import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.encryption import EncryptedType


class ReportType(str, enum.Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    COMBINED = "combined"


class PeriodType(str, enum.Enum):
    ANNUAL = "annual"
    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"


class FinancialReport(Base):
    """
    Hassas finansal veriler at-rest encryption ile korunur.
    Numeric alanlar EncryptedType ile şifrelenerek saklanır.
    """
    __tablename__ = "financial_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(Enum(ReportType), nullable=False)
    period = Column(Enum(PeriodType), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    source_document = Column(String(500), nullable=True)  # uploaded file path
    is_ai_generated = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)  # manually reviewed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- BİLANÇO (Balance Sheet) ---
    # Dönen Varlıklar (Current Assets) - encrypted
    cash_and_equivalents = Column(EncryptedType, nullable=True)
    short_term_investments = Column(EncryptedType, nullable=True)
    accounts_receivable = Column(EncryptedType, nullable=True)
    inventory = Column(EncryptedType, nullable=True)
    other_current_assets = Column(EncryptedType, nullable=True)
    total_current_assets = Column(EncryptedType, nullable=True)

    # Duran Varlıklar (Non-Current Assets)
    property_plant_equipment = Column(EncryptedType, nullable=True)
    intangible_assets = Column(EncryptedType, nullable=True)
    long_term_investments = Column(EncryptedType, nullable=True)
    total_non_current_assets = Column(EncryptedType, nullable=True)
    total_assets = Column(EncryptedType, nullable=True)

    # Kısa Vadeli Yükümlülükler (Current Liabilities)
    accounts_payable = Column(EncryptedType, nullable=True)
    short_term_debt = Column(EncryptedType, nullable=True)
    current_portion_long_term_debt = Column(EncryptedType, nullable=True)
    other_current_liabilities = Column(EncryptedType, nullable=True)
    total_current_liabilities = Column(EncryptedType, nullable=True)

    # Uzun Vadeli Yükümlülükler (Non-Current Liabilities)
    long_term_debt = Column(EncryptedType, nullable=True)
    deferred_tax_liabilities = Column(EncryptedType, nullable=True)
    total_non_current_liabilities = Column(EncryptedType, nullable=True)
    total_liabilities = Column(EncryptedType, nullable=True)

    # Öz Kaynaklar (Equity)
    share_capital = Column(EncryptedType, nullable=True)
    retained_earnings = Column(EncryptedType, nullable=True)
    other_equity = Column(EncryptedType, nullable=True)
    total_equity = Column(EncryptedType, nullable=True)

    # --- GELİR TABLOSU (Income Statement) ---
    revenue = Column(EncryptedType, nullable=True)
    cost_of_goods_sold = Column(EncryptedType, nullable=True)
    gross_profit = Column(EncryptedType, nullable=True)
    operating_expenses = Column(EncryptedType, nullable=True)
    ebitda = Column(EncryptedType, nullable=True)
    ebit = Column(EncryptedType, nullable=True)
    interest_expense = Column(EncryptedType, nullable=True)
    income_before_tax = Column(EncryptedType, nullable=True)
    income_tax = Column(EncryptedType, nullable=True)
    net_income = Column(EncryptedType, nullable=True)

    # --- NAKİT AKIŞI (Cash Flow) ---
    operating_cash_flow = Column(EncryptedType, nullable=True)
    investing_cash_flow = Column(EncryptedType, nullable=True)
    financing_cash_flow = Column(EncryptedType, nullable=True)
    free_cash_flow = Column(EncryptedType, nullable=True)
    net_change_in_cash = Column(EncryptedType, nullable=True)

    # AI Analiz Sonuçları (JSON)
    ai_analysis = Column(JSON, nullable=True)
    ai_ratios = Column(JSON, nullable=True)

    # --- EK VERİ ALANLARI (T4.3) ---
    banks_data = Column(JSON, nullable=True)        # Banka bazlı bakiye ve kredi limiti ozeti
    collections_data = Column(JSON, nullable=True)  # Bekleyen ve yapılan tahsilatlar
    debts_credits_data = Column(JSON, nullable=True)# Borc / Alacak ozeti ve vadeler
    projects_data = Column(JSON, nullable=True)     # Devam eden ve biten isler/projeler
    activity_conditions = Column(Text, nullable=True)# Alis-satis kosulları

    company = relationship("Company", back_populates="financial_reports")

    __table_args__ = (
        Index("ix_financial_company_year", "company_id", "fiscal_year"),
        Index("ix_financial_company_period", "company_id", "period"),
        Index("ix_financial_type_year", "report_type", "fiscal_year"),
        Index("ix_financial_company_type_year", "company_id", "report_type", "fiscal_year"),
    )

    def __repr__(self) -> str:
        return f"<FinancialReport id={self.id} company_id={self.company_id} year={self.fiscal_year}>"
