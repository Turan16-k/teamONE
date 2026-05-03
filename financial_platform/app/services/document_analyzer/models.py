"""
Veri modelleri — document_analyzer modülünün ortak tipleri.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AnalysisTier(str, Enum):
    BASIC = "basic"               # Başlangıç: metin özet + JSON
    PROFESSIONAL = "professional"  # Profesyonel: + grafikler + PDF rapor
    ENTERPRISE = "enterprise"      # Kurumsal: + PPTX + Excel + kapsamlı analiz


class DocumentType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    EXCEL = "excel"
    CSV = "csv"
    WORD = "word"
    TEXT = "text"
    UNKNOWN = "unknown"


class ExtractedDocument(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    filename: str
    file_type: DocumentType
    text_content: str = ""
    tables: List[List[Any]] = Field(default_factory=list)
    raw_bytes: Optional[bytes] = None   # scanned PDF / görsel → OCR için
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FinancialMetrics(BaseModel):
    revenue: Optional[float] = None
    expenses: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    period: Optional[str] = None
    currency: str = "TRY"


class DocumentSummary(BaseModel):
    filename: str
    document_type: str = ""
    brief_summary: str = ""
    key_findings: List[str] = Field(default_factory=list)
    financial_data: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    tier: AnalysisTier
    document_count: int
    total_text_chars: int = 0
    executive_summary: str
    document_summaries: List[DocumentSummary] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    financial_metrics: Optional[FinancialMetrics] = None
    detailed_analysis: Optional[str] = None    # Professional+
    recommendations: List[str] = Field(default_factory=list)  # Enterprise
    anomalies: List[str] = Field(default_factory=list)        # Enterprise
    report_files: Dict[str, bytes] = Field(default_factory=dict)


# Paket adı → tier eşleşmesi (platform entegrasyonu için)
PACKAGE_TO_TIER: Dict[str, AnalysisTier] = {
    "Başlangıç":     AnalysisTier.BASIC,
    "Profesyonel":   AnalysisTier.PROFESSIONAL,
    "Kurumsal":      AnalysisTier.ENTERPRISE,
    "basic":         AnalysisTier.BASIC,
    "professional":  AnalysisTier.PROFESSIONAL,
    "enterprise":    AnalysisTier.ENTERPRISE,
}
