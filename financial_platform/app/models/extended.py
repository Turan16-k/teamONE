import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Enum, Date, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.utils.encryption import EncryptedType


class CollectionType(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class ProjectStatus(str, enum.Enum):
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InvestmentStatus(str, enum.Enum):
    ACTIVE = "active"
    PLANNED = "planned"
    EXITED = "exited"


class CompanyBank(Base):
    __tablename__ = "company_banks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_no = Column(String(100), nullable=True)
    currency = Column(String(10), default="TRY", nullable=False)
    balance = Column(EncryptedType, nullable=True)
    credit_limit = Column(EncryptedType, nullable=True)
    credit_usage = Column(EncryptedType, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="banks")

    __table_args__ = (
        Index("ix_banks_company_id", "company_id"),
    )


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    collection_type = Column(Enum(CollectionType), nullable=False)
    amount = Column(EncryptedType, nullable=False)
    description = Column(Text, nullable=True)
    counterparty = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    collection_date = Column(Date, nullable=True)
    is_overdue = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="collections")

    __table_args__ = (
        Index("ix_collections_company_id", "company_id"),
        Index("ix_collections_type", "collection_type"),
        Index("ix_collections_company_type", "company_id", "collection_type"),
    )


class CompanyProject(Base):
    __tablename__ = "company_projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.ONGOING)
    client_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    value = Column(EncryptedType, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="projects")

    __table_args__ = (
        Index("ix_projects_company_id", "company_id"),
        Index("ix_projects_status", "status"),
    )


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    investment_type = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    geography = Column(String(100), nullable=True)
    status = Column(Enum(InvestmentStatus), nullable=False, default=InvestmentStatus.ACTIVE)

    purchase_value = Column(EncryptedType, nullable=True)
    current_value = Column(EncryptedType, nullable=True)
    planned_return_pct = Column(String(20), nullable=True)
    risk_score = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)
    purchase_date = Column(Date, nullable=True)
    exit_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="investments")

    __table_args__ = (
        Index("ix_investments_company_id", "company_id"),
        Index("ix_investments_status", "status"),
    )
