from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.encryption import EncryptedType


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=True)
    commercial_register_number = Column(String(100), nullable=True)
    establishment_date = Column(DateTime, nullable=True)
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    authorized_person_name = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    
    # Financial summary for the company (Encrypted as per T10/9.2)
    # Using String/Text as base for encryption utility
    annual_turnover_estimate = Column(EncryptedType, nullable=True)
    
    # Contract details (T6)
    contract_value = Column(EncryptedType, nullable=True)
    contract_start_date = Column(DateTime, nullable=True)
    contract_end_date = Column(DateTime, nullable=True)
    contract_type = Column(String(100), nullable=True) # Rapor, Analiz, Sistem, Diger
    
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="companies")
    financial_reports = relationship(
        "FinancialReport", back_populates="company",
        lazy="select", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_companies_name", "name"),
        Index("ix_companies_owner_id", "owner_id"),
        Index("ix_companies_owner_name", "owner_id", "name"),
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name}>"
