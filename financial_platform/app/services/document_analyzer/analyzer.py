"""
Gemini AI analiz katmanı — tier'a göre farklı prompt + çıktı.
"""
from __future__ import annotations
import json
import base64
import logging
import re
from typing import List

import google.generativeai as genai

from .models import ExtractedDocument, DocumentType, AnalysisTier

logger = logging.getLogger(__name__)

_SYSTEM_BASIC = """Sen finansal belge analisti asistanısın. Türkçe veya İngilizce belgeleri anlayabilirsin.
Verilen belgelerden kısa özetler ve ana bulgular çıkar. Her zaman Türkçe yanıt ver."""

_SYSTEM_PROFESSIONAL = """Sen uzman finansal analist asistanısın. Finansal tablolar, fişler, raporlar ve
belgelerden:
- Ayrıntılı finansal metrikleri çıkar (gelir, gider, kâr, varlık, borç, özkaynak, nakit akışı)
- Dönem bilgilerini ve para birimini tespit et
- Önemli bulguları ve riskleri belirle
Her zaman Türkçe yanıt ver."""

_SYSTEM_ENTERPRISE = """Sen kurumsal düzey CFO asistanısın. Kapsamlı finansal analiz için:
- Tüm finansal metrikleri ve finansal oranları hesapla
- Trend, anomali ve risk tespiti yap
- Sektörel karşılaştırma değerlendirmesi yap
- Stratejik iyileştirme önerileri sun
- Hem belge bazı hem portföy geneli değerlendirme yap
Her zaman Türkçe yanıt ver."""


class GeminiAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-1.5-pro")

    # ── public ────────────────────────────────────────────────────────────

    def analyze_documents(
        self,
        documents: List[ExtractedDocument],
        tier: AnalysisTier,
    ) -> dict:
        # Taranmış belgeler için OCR çalıştır
        for doc in documents:
            if doc.raw_bytes and not doc.text_content.strip():
                doc.text_content = self._ocr(doc)

        if tier == AnalysisTier.BASIC:
            return self._basic(documents)
        elif tier == AnalysisTier.PROFESSIONAL:
            return self._professional(documents)
        else:
            return self._enterprise(documents)

    # ── OCR ───────────────────────────────────────────────────────────────

    def _ocr(self, doc: ExtractedDocument) -> str:
        if not doc.raw_bytes:
            return doc.text_content
        suffix = doc.filename.rsplit(".", 1)[-1].lower()
        if doc.file_type == DocumentType.PDF:
            mime = "application/pdf"
        elif suffix in ("jpg", "jpeg"):
            mime = "image/jpeg"
        elif suffix == "png":
            mime = "image/png"
        elif suffix == "webp":
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        try:
            part = {
                "inline_data": {
                    "mime_type": mime,
                    "data": base64.b64encode(doc.raw_bytes).decode(),
                }
            }
            resp = self._model.generate_content([
                part,
                ("Bu belgeden tüm metni, tabloları, sayıları ve tarihleri çıkar. "
                 "Tablo yapısını koru, finansal verileri vurgula."),
            ])
            return resp.text
        except Exception as exc:
            logger.warning("OCR başarısız %s: %s", doc.filename, exc)
            return f"[OCR başarısız: {exc}]"

    # ── context builder ───────────────────────────────────────────────────

    def _ctx(self, documents: List[ExtractedDocument], max_per_doc: int = 3000) -> str:
        parts = []
        for i, doc in enumerate(documents, 1):
            snippet = doc.text_content[:max_per_doc]
            parts.append(f"=== BELGE {i}: {doc.filename} ===\n{snippet}")
        return "\n\n".join(parts)

    # ── tier prompts ──────────────────────────────────────────────────────

    def _basic(self, docs: List[ExtractedDocument]) -> dict:
        ctx = self._ctx(docs, 2000)
        prompt = f"""{_SYSTEM_BASIC}

Aşağıdaki {len(docs)} belgeyi analiz et:

{ctx}

JSON formatında yanıtla (başka metin ekleme):
{{
  "executive_summary": "Tüm belgeler için 3-5 cümlelik genel özet",
  "document_summaries": [
    {{"filename": "...", "document_type": "fatura/rapor/fiş/vb", "brief_summary": "1-2 cümle", "key_findings": ["bulgu1", "bulgu2"], "financial_data": {{}}}}
  ],
  "key_insights": ["insight1", "insight2", "insight3"]
}}"""
        return self._call(prompt, {
            "executive_summary": "Belgeler analiz edildi.",
            "document_summaries": [],
            "key_insights": [],
        })

    def _professional(self, docs: List[ExtractedDocument]) -> dict:
        ctx = self._ctx(docs, 4000)
        prompt = f"""{_SYSTEM_PROFESSIONAL}

Aşağıdaki {len(docs)} belgeyi profesyonel düzeyde analiz et:

{ctx}

JSON formatında yanıtla (başka metin ekleme):
{{
  "executive_summary": "5-8 cümlelik kapsamlı genel özet",
  "document_summaries": [
    {{
      "filename": "...",
      "document_type": "fatura/rapor/beyan/fiş/vb",
      "brief_summary": "3-4 cümle",
      "key_findings": ["bulgu1", "bulgu2", "bulgu3"],
      "financial_data": {{"gelir": null, "gider": null, "net_kar": null, "toplam_tutar": null, "donem": null}}
    }}
  ],
  "key_insights": ["insight1", "insight2", "insight3", "insight4", "insight5"],
  "financial_metrics": {{
    "revenue": null, "expenses": null, "net_income": null,
    "total_assets": null, "total_liabilities": null, "total_equity": null,
    "operating_cash_flow": null, "period": null, "currency": "TRY"
  }},
  "chart_data": {{
    "revenue_expense": {{"labels": [], "revenue": [], "expenses": []}},
    "category_breakdown": {{"labels": [], "values": []}},
    "monthly_trend": {{"months": [], "values": []}}
  }}
}}"""
        return self._call(prompt, {
            "executive_summary": "Belgeler profesyonel düzeyde analiz edildi.",
            "document_summaries": [], "key_insights": [],
            "financial_metrics": {}, "chart_data": {},
        })

    def _enterprise(self, docs: List[ExtractedDocument]) -> dict:
        ctx = self._ctx(docs, 6000)
        prompt = f"""{_SYSTEM_ENTERPRISE}

Aşağıdaki {len(docs)} belgeyi kurumsal düzeyde kapsamlı analiz et:

{ctx}

JSON formatında yanıtla (başka metin ekleme):
{{
  "executive_summary": "8-12 cümlelik üst düzey yönetici özeti, stratejik değerlendirme içermeli",
  "detailed_analysis": "Minimum 400 kelimelik kapsamlı finansal analiz metni",
  "document_summaries": [
    {{
      "filename": "...",
      "document_type": "fatura/rapor/beyan/fiş/vb",
      "brief_summary": "5-6 cümle",
      "key_findings": ["bulgu1", "bulgu2", "bulgu3", "bulgu4"],
      "financial_data": {{"gelir": null, "gider": null, "net_kar": null, "toplam_tutar": null, "donem": null, "notlar": ""}}
    }}
  ],
  "key_insights": ["insight1", "insight2", "insight3", "insight4", "insight5", "insight6"],
  "recommendations": ["öneri1", "öneri2", "öneri3", "öneri4"],
  "anomalies": ["anomali/risk1", "anomali/risk2"],
  "financial_metrics": {{
    "revenue": null, "expenses": null, "net_income": null,
    "total_assets": null, "total_liabilities": null, "total_equity": null,
    "operating_cash_flow": null, "period": null, "currency": "TRY"
  }},
  "chart_data": {{
    "revenue_expense": {{"labels": [], "revenue": [], "expenses": []}},
    "category_breakdown": {{"labels": [], "values": []}},
    "monthly_trend": {{"months": [], "values": []}},
    "asset_structure": {{
      "labels": ["Dönen Varlıklar", "Duran Varlıklar", "Kısa Vadeli Borç", "Uzun Vadeli Borç", "Özkaynak"],
      "values": [null, null, null, null, null]
    }},
    "cash_flow": {{"categories": ["İşletme", "Yatırım", "Finansman"], "values": [null, null, null]}}
  }},
  "ratio_analysis": {{
    "current_ratio": null,
    "debt_to_equity": null,
    "profit_margin": null,
    "return_on_equity": null,
    "asset_turnover": null
  }}
}}"""
        return self._call(prompt, {
            "executive_summary": "Belgeler kurumsal düzeyde analiz edildi.",
            "detailed_analysis": "Analiz gerçekleştirildi.",
            "document_summaries": [], "key_insights": [],
            "recommendations": [], "anomalies": [],
            "financial_metrics": {}, "chart_data": {}, "ratio_analysis": {},
        })

    # ── Gemini çağrısı ────────────────────────────────────────────────────

    def _call(self, prompt: str, fallback: dict) -> dict:
        try:
            resp = self._model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.15,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(resp.text)
        except Exception:
            # response_mime_type desteklenmiyorsa JSON'ı manuel çıkar
            try:
                resp = self._model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.15),
                )
                text = resp.text
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except Exception as exc2:
                logger.error("Gemini API hatası: %s", exc2)
        return fallback
