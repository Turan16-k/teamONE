"""
T3: OCR/AI Pipeline — Google Gemini 1.5 Pro multimodal API.
PDF veya görsel yüklendiğinde yapılandırılmamış finansal tablodan
yapılandırılmış form verisi üretilir.
"""
import base64
import json
import time
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.config import settings
from app.utils.logging import log_ai_operation

FINANCIAL_EXTRACTION_PROMPT = """
Sen bir finansal analiz uzmanısın. Sana verilen belge (bilanço, gelir tablosu veya nakit akışı tablosu)
içindeki tüm finansal verileri yapılandırılmış JSON formatında çıkar.

ÇIKTI FORMATI (sadece JSON, başka bir şey yazma):
{
  "report_type": "balance_sheet | income_statement | cash_flow | combined",
  "fiscal_year": <yıl int>,
  "period": "annual | q1 | q2 | q3 | q4",
  "currency": "TRY | USD | EUR",
  "balance_sheet": {
    "cash_and_equivalents": <sayı veya null>,
    "short_term_investments": <sayı veya null>,
    "accounts_receivable": <sayı veya null>,
    "inventory": <sayı veya null>,
    "other_current_assets": <sayı veya null>,
    "total_current_assets": <sayı veya null>,
    "property_plant_equipment": <sayı veya null>,
    "intangible_assets": <sayı veya null>,
    "long_term_investments": <sayı veya null>,
    "total_non_current_assets": <sayı veya null>,
    "total_assets": <sayı veya null>,
    "accounts_payable": <sayı veya null>,
    "short_term_debt": <sayı veya null>,
    "current_portion_long_term_debt": <sayı veya null>,
    "other_current_liabilities": <sayı veya null>,
    "total_current_liabilities": <sayı veya null>,
    "long_term_debt": <sayı veya null>,
    "deferred_tax_liabilities": <sayı veya null>,
    "total_non_current_liabilities": <sayı veya null>,
    "total_liabilities": <sayı veya null>,
    "share_capital": <sayı veya null>,
    "retained_earnings": <sayı veya null>,
    "other_equity": <sayı veya null>,
    "total_equity": <sayı veya null>
  },
  "income_statement": {
    "revenue": <sayı veya null>,
    "cost_of_goods_sold": <sayı veya null>,
    "gross_profit": <sayı veya null>,
    "operating_expenses": <sayı veya null>,
    "ebitda": <sayı veya null>,
    "ebit": <sayı veya null>,
    "interest_expense": <sayı veya null>,
    "income_before_tax": <sayı veya null>,
    "income_tax": <sayı veya null>,
    "net_income": <sayı veya null>
  },
  "cash_flow": {
    "operating_cash_flow": <sayı veya null>,
    "investing_cash_flow": <sayı veya null>,
    "financing_cash_flow": <sayı veya null>,
    "free_cash_flow": <sayı veya null>,
    "net_change_in_cash": <sayı veya null>
  },
  "confidence_score": <0.0-1.0 arası güven skoru>,
  "notes": "<çıkarılamayan veya belirsiz alanlar>"
}

Sayıları tam sayı veya ondalık olarak ver (virgül değil nokta kullan).
Belgede olmayan alanlar için null kullan. Sadece JSON döndür.
"""

FINANCIAL_ANALYSIS_PROMPT = """
Sen deneyimli bir finansal analistsin. Aşağıdaki finansal verileri analiz et ve
kapsamlı rasyo hesaplamaları ile değerlendirme yap.

FİNANSAL VERİLER:
{financial_data}

Aşağıdaki analizleri JSON formatında üret (sadece JSON):
{{
  "liquidity": {{
    "current_ratio": <dönen varlıklar / kısa vadeli yükümlülükler>,
    "quick_ratio": <(dönen varlıklar - stok) / kısa vadeli yükümlülükler>,
    "cash_ratio": <nakit / kısa vadeli yükümlülükler>,
    "assessment": "<likidite durumu değerlendirmesi>"
  }},
  "leverage": {{
    "debt_to_equity": <toplam borç / özkaynak>,
    "debt_to_assets": <toplam borç / toplam varlıklar>,
    "equity_ratio": <özkaynak / toplam varlıklar>,
    "interest_coverage": <EBIT / faiz gideri>,
    "assessment": "<kaldıraç değerlendirmesi>"
  }},
  "profitability": {{
    "gross_margin": <brüt kar / gelir>,
    "net_margin": <net kar / gelir>,
    "ebitda_margin": <EBITDA / gelir>,
    "roa": <net kar / toplam varlıklar>,
    "roe": <net kar / özkaynak>,
    "assessment": "<kârlılık değerlendirmesi>"
  }},
  "efficiency": {{
    "asset_turnover": <gelir / toplam varlıklar>,
    "receivables_turnover": <gelir / alacaklar>,
    "inventory_turnover": <satılan malın maliyeti / stok>,
    "assessment": "<etkinlik değerlendirmesi>"
  }},
  "overall_assessment": "<genel değerlendirme>",
  "financial_score": <1-100 arası toplam sağlık skoru int>,
  "risk_indicators": ["<risk 1>", "<risk 2>"],
  "positive_indicators": ["<güçlü yön 1>", "<güçlü yön 2>"]
}}

Hesaplama yapılamayan rasyolar için null kullan. Sadece JSON döndür.
"""


def _clean_json(raw: str) -> str:
    if "```json" in raw:
        return raw.split("```json")[1].split("```")[0].strip()
    if "```" in raw:
        return raw.split("```")[1].split("```")[0].strip()
    return raw.strip()


class AIService:
    def __init__(self) -> None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-1.5-pro"
        self._generation_config = GenerationConfig(
            temperature=0.1,       # finansal veri için düşük yaratıcılık
            top_p=0.95,
            max_output_tokens=4096,
        )

    def _get_model(self) -> genai.GenerativeModel:
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self._generation_config,
        )

    def extract_financial_data_from_document(
        self,
        file_path: str,
        file_content: bytes,
        media_type: str,
        db,
        user_id: Optional[int] = None,
    ) -> dict:
        """
        T3: PDF veya görsel belge → Gemini multimodal → yapılandırılmış JSON.
        Hem OCR hem parsing tek API çağrısında gerçekleşir.
        """
        start_time = time.time()
        file_name = Path(file_path).name

        try:
            encoded = base64.b64encode(file_content).decode("utf-8")
            model = self._get_model()

            response = model.generate_content([
                {"mime_type": media_type, "data": encoded},
                FINANCIAL_EXTRACTION_PROMPT,
            ])

            duration_ms = (time.time() - start_time) * 1000
            result = json.loads(_clean_json(response.text))

            usage = response.usage_metadata
            log_ai_operation(
                db=db,
                user_id=user_id,
                service="ocr_extraction",
                model_used=self.model_name,
                prompt_tokens=getattr(usage, "prompt_token_count", None),
                completion_tokens=getattr(usage, "candidates_token_count", None),
                duration_ms=duration_ms,
                success=True,
                request_metadata={"file_name": file_name, "media_type": media_type},
                response_metadata={
                    "confidence_score": result.get("confidence_score"),
                    "report_type": result.get("report_type"),
                },
            )
            return result

        except json.JSONDecodeError as e:
            duration_ms = (time.time() - start_time) * 1000
            log_ai_operation(
                db=db, user_id=user_id, service="ocr_extraction",
                model_used=self.model_name, duration_ms=duration_ms, success=False,
                error_type="JSONDecodeError", error_message=str(e),
                request_metadata={"file_name": file_name},
            )
            raise ValueError(f"Gemini yanıtı JSON formatında değil: {e}")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_ai_operation(
                db=db, user_id=user_id, service="ocr_extraction",
                model_used=self.model_name, duration_ms=duration_ms, success=False,
                error_type=type(e).__name__, error_message=str(e),
                request_metadata={"file_name": file_name},
            )
            raise

    def analyze_financial_ratios(
        self,
        financial_data: dict,
        db,
        user_id: Optional[int] = None,
    ) -> dict:
        """
        T3: Analitik Modül — likidite, kaldıraç, kârlılık, etkinlik rasyoları.
        LLM girdi olarak ham finansal veri alır, yorumlanmış analiz üretir.
        """
        start_time = time.time()

        try:
            formatted = json.dumps(financial_data, ensure_ascii=False, indent=2, default=str)
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(financial_data=formatted)

            model = self._get_model()
            response = model.generate_content(prompt)
            duration_ms = (time.time() - start_time) * 1000

            result = json.loads(_clean_json(response.text))

            usage = response.usage_metadata
            log_ai_operation(
                db=db, user_id=user_id, service="financial_analysis",
                model_used=self.model_name,
                prompt_tokens=getattr(usage, "prompt_token_count", None),
                completion_tokens=getattr(usage, "candidates_token_count", None),
                duration_ms=duration_ms, success=True,
            )
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_ai_operation(
                db=db, user_id=user_id, service="financial_analysis",
                model_used=self.model_name, duration_ms=duration_ms, success=False,
                error_type=type(e).__name__, error_message=str(e),
            )
            raise


ai_service = AIService()
