import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Enum, Date
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.encryption import EncryptedType


class ContractType(str, enum.Enum):
    REPORT = "report"
    ANALYSIS = "analysis"
    SYSTEM = "system"
    OTHER = "other"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=True)
    trade_registry_no = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Kuruluş & İletişim
    founding_date = Column(Date, nullable=True)
    authorized_person_name = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # Ciro (şifrelendi)
    annual_revenue_estimate = Column(EncryptedType, nullable=True)
    annual_revenue_actual = Column(EncryptedType, nullable=True)

    # Sözleşme bilgileri
    contract_amount = Column(EncryptedType, nullable=True)
    contract_start = Column(Date, nullable=True)
    contract_end = Column(Date, nullable=True)
    contract_type = Column(Enum(ContractType), nullable=True)

    # Alt firma desteği
    parent_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="companies")
    financial_reports = relationship(
        "FinancialReport", back_populates="company",
        lazy="select", cascade="all, delete-orphan"
    )
    banks = relationship("CompanyBank", back_populates="company", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("CompanyProject", back_populates="company", cascade="all, delete-orphan")
    investments = relationship("Investment", back_populates="company", cascade="all, delete-orphan")
    sub_companies = relationship("Company", foreign_keys=[parent_company_id])

    __table_args__ = (
        Index("ix_companies_name", "name"),
        Index("ix_companies_owner_id", "owner_id"),
        Index("ix_companies_owner_name", "owner_id", "name"),
        Index("ix_companies_contract_end", "contract_end"),
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name}>"
