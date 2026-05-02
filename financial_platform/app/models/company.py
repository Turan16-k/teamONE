from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=True)
    sector = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
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
