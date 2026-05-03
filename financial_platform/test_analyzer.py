"""Test script — Gemini API olmadan extractor + charts + reporter doğrular."""
import io, zipfile, sys
sys.path.insert(0, ".")

# Test ZIP oluştur
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as zf:
    zf.writestr("gelir_tablosu.csv",
        "Kalem,2024,2023\nGelir,1500000,1200000\nGider,900000,750000\nNet Kar,600000,450000\n")
    zf.writestr("bilanco_notu.txt",
        "Toplam Varlik: 5.200.000 TRY\nToplam Borc: 2.100.000 TRY\nOzkaynak: 3.100.000 TRY\nDonem: 2024\n")
    zf.writestr("nakit_akisi.txt",
        "Isletme: +850.000 TRY\nYatirim: -320.000 TRY\nFinansman: +150.000 TRY\n")
zip_bytes = buf.getvalue()
print(f"Test ZIP: {len(zip_bytes)} bayt, 3 dosya")

# 1 — Extractor
from app.services.document_analyzer.extractor import ZipExtractor
docs = ZipExtractor().extract_all(zip_bytes)
print(f"Extracted: {[d.filename for d in docs]}")
assert len(docs) == 3

# 2 — Charts
from app.services.document_analyzer.charts import ChartGenerator
chart_data = {
    "revenue_expense": {
        "labels": ["2023", "2024"],
        "revenue":  [1_200_000, 1_500_000],
        "expenses": [750_000,   900_000],
    },
    "category_breakdown": {
        "labels": ["Personel", "Kira", "Hammadde", "Diger"],
        "values": [400_000, 150_000, 280_000, 70_000],
    },
    "monthly_trend": {
        "months": ["Oca", "Sub", "Mar", "Nis", "May", "Haz"],
        "values": [100_000, 120_000, 95_000, 140_000, 130_000, 160_000],
    },
}
charts = ChartGenerator().generate(chart_data, tier="professional")
print(f"Charts: {list(charts.keys())}")
assert len(charts) == 3
for name, data in charts.items():
    kb = len(data) // 1024
    print(f"  {name}: {kb} KB")
    assert kb > 5, f"Grafik cok kucuk: {name}"

# 3 — Reporter
from app.services.document_analyzer.models import (
    AnalysisTier, AnalysisResult, DocumentSummary, FinancialMetrics
)
from app.services.document_analyzer.reporter import TieredReporter

result = AnalysisResult(
    tier=AnalysisTier.PROFESSIONAL,
    document_count=3,
    executive_summary=(
        "Sirket 2024 yilinda bir onceki yila kiyasla yuzde 25 gelir artisi kaydetmistir. "
        "Net kar 600.000 TRY seviyesine ulasarak guclu bir performans sergilenmistir."
    ),
    document_summaries=[
        DocumentSummary(
            filename="gelir_tablosu.csv",
            document_type="finansal tablo",
            brief_summary="2023-2024 gelir ve gider karsilastirmasi.",
            key_findings=["Gelir yuzde 25 artti", "Gider yuzde 20 artti"],
        ),
    ],
    key_insights=["Gelir buyume hizi gider buyume hizini geciyor.", "Guclu ozkaynak yapisi."],
    financial_metrics=FinancialMetrics(
        revenue=1_500_000, expenses=900_000, net_income=600_000,
        total_assets=5_200_000, total_liabilities=2_100_000, total_equity=3_100_000,
        period="2024", currency="TRY",
    ),
)

files = TieredReporter().generate(result, charts, {})
print(f"\nGenerated files: {list(files.keys())}")

json_bytes = files.get("analiz_sonucu.json", b"")
pdf_bytes  = files.get("finansal_rapor.pdf", b"")
print(f"  JSON : {len(json_bytes)} bayt")
print(f"  PDF  : {len(pdf_bytes)} bayt")

assert len(json_bytes) > 100, "JSON bos!"
assert len(pdf_bytes)  > 500, "PDF bos!"

# JSON gecerlilik
import json
parsed = json.loads(json_bytes)
assert parsed["ozet"] == result.executive_summary
assert parsed["finansal_metrikler"]["revenue"] == 1_500_000.0
print(f"  JSON gecerli: ozet={parsed['ozet'][:40]}...")

print("\nTUM TESTLER BASARILI!")
