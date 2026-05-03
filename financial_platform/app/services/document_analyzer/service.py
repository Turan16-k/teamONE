"""
Ana orkestrasyon servisi.
Kullanım:
    svc = DocumentAnalyzerService(api_key="...")
    result = svc.analyze_zip(zip_bytes, tier="professional")
    result.report_files  # {"finansal_rapor.pdf": bytes, ...}
"""
from __future__ import annotations
import logging
from typing import Union

from .models import (
    AnalysisTier, AnalysisResult, DocumentSummary,
    FinancialMetrics, PACKAGE_TO_TIER,
)
from .extractor import ZipExtractor
from .analyzer  import GeminiAnalyzer
from .charts    import ChartGenerator
from .reporter  import TieredReporter

logger = logging.getLogger(__name__)


class DocumentAnalyzerService:
    """
    ZIP dosyasındaki tüm belgeleri okur, AI ile analiz eder ve
    tier'a göre çıktı dosyaları üretir.

    Tierlar:
        basic        → JSON özet
        professional → JSON + grafikler + PDF rapor
        enterprise   → JSON + grafikler + PDF + PPTX sunum + Excel çalışma kitabı
    """

    def __init__(self, api_key: str):
        self._extractor = ZipExtractor()
        self._analyzer  = GeminiAnalyzer(api_key=api_key)
        self._charts    = ChartGenerator()
        self._reporter  = TieredReporter()

    # ── ana metod ─────────────────────────────────────────────────────────

    def analyze_zip(
        self,
        zip_bytes: bytes,
        tier: Union[str, AnalysisTier] = AnalysisTier.PROFESSIONAL,
    ) -> AnalysisResult:
        """
        zip_bytes : ZIP dosyasının ham baytları
        tier      : "basic" | "professional" | "enterprise"
                    veya paket adı: "Başlangıç" | "Profesyonel" | "Kurumsal"
        """
        if isinstance(tier, str):
            tier = PACKAGE_TO_TIER.get(tier, AnalysisTier.PROFESSIONAL)

        logger.info("Analiz başladı — tier=%s boyut=%dKB", tier.value, len(zip_bytes) // 1024)

        # 1 — Belgeleri çıkar
        docs = self._extractor.extract_all(zip_bytes)
        if not docs:
            return AnalysisResult(
                tier=tier,
                document_count=0,
                executive_summary="ZIP dosyasında işlenebilir belge bulunamadı.",
                key_insights=["Desteklenen formatlar: PDF, Excel, CSV, Word, görsel."],
            )

        total_chars = sum(len(d.text_content) for d in docs)
        logger.info("%d belge çıkarıldı, toplam %d karakter", len(docs), total_chars)

        # 2 — AI analizi
        raw = self._analyzer.analyze_documents(docs, tier)

        # 3 — Yapısal model oluştur
        doc_summaries = [
            DocumentSummary(
                filename=ds.get("filename", "unknown"),
                document_type=ds.get("document_type", ""),
                brief_summary=ds.get("brief_summary", ""),
                key_findings=ds.get("key_findings", []),
                financial_data=ds.get("financial_data", {}),
            )
            for ds in raw.get("document_summaries", [])
        ]

        fin_metrics = self._parse_metrics(raw.get("financial_metrics", {}))

        result = AnalysisResult(
            tier=tier,
            document_count=len(docs),
            total_text_chars=total_chars,
            executive_summary=raw.get("executive_summary", "Analiz tamamlandı."),
            document_summaries=doc_summaries,
            key_insights=raw.get("key_insights", []),
            financial_metrics=fin_metrics,
            detailed_analysis=raw.get("detailed_analysis"),
            recommendations=raw.get("recommendations", []),
            anomalies=raw.get("anomalies", []),
        )

        # 4 — Grafik üret (professional+)
        charts: dict = {}
        if tier in (AnalysisTier.PROFESSIONAL, AnalysisTier.ENTERPRISE):
            charts = self._charts.generate(
                chart_data=raw.get("chart_data", {}),
                tier=tier.value,
                ratio_data=raw.get("ratio_analysis") if tier == AnalysisTier.ENTERPRISE else None,
            )
            logger.info("%d grafik üretildi", len(charts))

        # 5 — Rapor dosyaları üret
        result.report_files = self._reporter.generate(result, charts, raw)
        logger.info("Analiz tamamlandı — %d dosya üretildi: %s",
                    len(result.report_files), list(result.report_files.keys()))

        return result

    # ── yardımcı ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_metrics(fm: dict) -> FinancialMetrics | None:
        if not fm or not any(v for k, v in fm.items() if k not in ("period", "currency")):
            return None
        numeric = {"revenue", "expenses", "net_income", "total_assets",
                   "total_liabilities", "total_equity", "operating_cash_flow"}
        parsed = {}
        for k, v in fm.items():
            if k in numeric:
                try:
                    parsed[k] = float(str(v).replace(",", "")) if v is not None else None
                except (ValueError, TypeError):
                    parsed[k] = None
            else:
                parsed[k] = v
        try:
            return FinancialMetrics(**parsed)
        except Exception as exc:
            logger.warning("Finansal metrik parse hatası: %s", exc)
            return None
