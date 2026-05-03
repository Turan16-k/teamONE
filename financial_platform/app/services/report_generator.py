"""
Kapsamlı görsel PDF rapor üretici.
Bilanço, gelir tablosu, nakit akışı, oranlar ve genişletilmiş verileri
grafiklerle birlikte tek A4 PDF'e derler.
"""
import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── renk sabitleri ────────────────────────────────────────────────────────────
_BLUE   = "#1565C0"
_LBLUE  = "#E3F2FD"
_GREEN  = "#2E7D32"
_LGREEN = "#E8F5E9"
_RED    = "#C62828"
_ORANGE = "#E65100"
_GRAY   = "#757575"
_LGRAY  = "#F5F5F5"
_PALETTE = [_BLUE, _GREEN, _ORANGE, "#9C27B0", "#FF9800", "#00BCD4", "#795548"]


def _to_float(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _fmt(v, currency: str = "TRY") -> str:
    if v is None:
        return "—"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    sym = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency)
    neg = "-" if v < 0 else ""
    av = abs(v)
    if av >= 1_000_000_000:
        return f"{neg}{sym}{av/1_000_000_000:.2f}Mn"
    if av >= 1_000_000:
        return f"{neg}{sym}{av/1_000_000:.2f}M"
    if av >= 1_000:
        return f"{neg}{sym}{av/1_000:.1f}K"
    return f"{neg}{sym}{av:.2f}"


# ── matplotlib yardımcıları ───────────────────────────────────────────────────

def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _save_fig(fig) -> bytes:
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _chart_asset_pie(report) -> bytes:
    current   = _to_float(report.total_current_assets) or 0
    noncurrent = _to_float(report.total_non_current_assets) or 0
    if current + noncurrent == 0:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 5))
    vals   = [current, noncurrent]
    labels = [f"Dönen Varlık\n{_fmt(current)}", f"Duran Varlık\n{_fmt(noncurrent)}"]
    wedges, texts, autos = ax.pie(
        vals, labels=labels, colors=[_BLUE, "#42A5F5"],
        autopct="%1.1f%%", startangle=90, pctdistance=0.80,
    )
    for t in autos:
        t.set_fontsize(9)
    ax.set_title("Varlık Yapısı", fontsize=12, fontweight="bold", pad=14)
    fig.tight_layout()
    return _save_fig(fig)


def _chart_balance_structure(report) -> bytes:
    items = [
        ("Toplam Varlık",        _to_float(report.total_assets),                  _BLUE),
        ("Kısa V. Yükümlülük",   _to_float(report.total_current_liabilities),     _RED),
        ("Uzun V. Yükümlülük",   _to_float(report.total_non_current_liabilities), _ORANGE),
        ("Özkaynak",             _to_float(report.total_equity),                  _GREEN),
    ]
    items = [(l, v, c) for l, v, c in items if v and v != 0]
    if not items:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 3.5))
    labels, vals, colors = zip(*items)
    bars = ax.barh(labels, [abs(v) for v in vals], color=colors, alpha=0.85, height=0.5)
    ax.set_title("Bilanço Yapısı", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Tutar")
    ax.grid(axis="x", alpha=0.3)
    for bar, v in zip(bars, vals):
        ax.annotate(_fmt(v), xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", va="center", fontsize=9)
    fig.tight_layout()
    return _save_fig(fig)


def _chart_income_bar(report) -> bytes:
    items_raw = [
        ("Gelir",    _to_float(report.revenue)),
        ("Brüt Kâr", _to_float(report.gross_profit)),
        ("EBITDA",   _to_float(report.ebitda)),
        ("EBIT",     _to_float(report.ebit)),
        ("Net Kâr",  _to_float(report.net_income)),
    ]
    items = [(l, v) for l, v in items_raw if v is not None]
    if len(items) < 2:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels, vals = zip(*items)
    colors = [_GREEN if v >= 0 else _RED for v in vals]
    bars = ax.bar(labels, vals, color=colors, alpha=0.85, width=0.55, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_title("Gelir Tablosu", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Tutar")
    ax.grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, vals):
        offset = abs(v) * 0.03 if v >= 0 else -abs(v) * 0.08
        ax.annotate(_fmt(v), xy=(bar.get_x() + bar.get_width() / 2, v + offset),
                    ha="center", fontsize=8.5, fontweight="bold")
    fig.tight_layout()
    return _save_fig(fig)


def _chart_cashflow(report) -> bytes:
    raw = [
        ("İşletme",    _to_float(report.operating_cash_flow)),
        ("Yatırım",    _to_float(report.investing_cash_flow)),
        ("Finansman",  _to_float(report.financing_cash_flow)),
    ]
    items = [(l, v) for l, v in raw if v is not None]
    if not items:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels, vals = zip(*items)
    colors = [_GREEN if v >= 0 else _RED for v in vals]
    bars = ax.bar(labels, vals, color=colors, alpha=0.85, width=0.45, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_title("Nakit Akış Analizi", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Tutar")
    ax.grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, vals):
        offset = 6 if v >= 0 else -16
        ax.annotate(_fmt(v), xy=(bar.get_x() + bar.get_width() / 2, v),
                    xytext=(0, offset), textcoords="offset points",
                    ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    return _save_fig(fig)


def _chart_ratio_radar(ai_ratios: dict) -> bytes:
    import numpy as np
    liq  = ai_ratios.get("liquidity", {})
    prof = ai_ratios.get("profitability", {})

    def _cap(v):
        try:
            return min(max(float(v), 0), 5.0) if v is not None else 0
        except (TypeError, ValueError):
            return 0

    metrics = {
        "Cari Oran":   _cap(liq.get("current_ratio")),
        "Hızlı Oran":  _cap(liq.get("quick_ratio")),
        "Brüt Marj":   _cap(prof.get("gross_margin")),
        "Net Marj":    _cap(prof.get("net_margin")),
        "ROE":         _cap(prof.get("roe")),
        "ROA":         _cap(prof.get("roa")),
    }
    metrics = {k: v for k, v in metrics.items() if v > 0}
    if len(metrics) < 3:
        return b""

    plt = _plt()
    labels = list(metrics.keys())
    vals   = list(metrics.values())
    n      = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles_plot = angles + angles[:1]
    vals_plot   = vals   + vals[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles_plot, vals_plot, "o-", linewidth=2.2, color=_BLUE)
    ax.fill(angles_plot, vals_plot, alpha=0.18, color=_BLUE)
    ax.set_thetagrids(
        [a * 180 / np.pi for a in angles],
        labels, fontsize=10,
    )
    ax.set_title("Finansal Oran Profili", fontsize=12, fontweight="bold", pad=20)
    fig.tight_layout()
    return _save_fig(fig)


def _chart_collections(collections) -> bytes:
    if not collections:
        return b""
    pending   = sum(_to_float(c.amount) or 0 for c in collections if c.collection_type.value == "pending")
    completed = sum(_to_float(c.amount) or 0 for c in collections if c.collection_type.value == "completed")
    if pending + completed == 0:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4))
    vals = [pending, completed]
    bars = ax.bar(["Bekleyen", "Tamamlanan"], vals, color=[_ORANGE, _GREEN], alpha=0.85, width=0.4)
    ax.set_title("Tahsilat Durumu", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Toplam Tutar")
    ax.grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.annotate(_fmt(v), xy=(bar.get_x() + bar.get_width() / 2, v),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    return _save_fig(fig)


def _chart_investments(investments) -> bytes:
    if not investments:
        return b""
    portfolio: dict = {}
    for inv in investments:
        key = inv.sector or inv.investment_type or "Diğer"
        val = _to_float(inv.current_value) or _to_float(inv.purchase_value) or 0
        portfolio[key] = portfolio.get(key, 0) + val
    portfolio = {k: v for k, v in portfolio.items() if v > 0}
    if not portfolio:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 5))
    labels = list(portfolio.keys())
    vals   = list(portfolio.values())
    ax.pie(vals, labels=labels, colors=_PALETTE[:len(vals)],
           autopct="%1.1f%%", startangle=90, pctdistance=0.80)
    ax.set_title("Yatırım Portföyü", fontsize=12, fontweight="bold", pad=14)
    fig.tight_layout()
    return _save_fig(fig)


def _chart_bank_balances(banks) -> bytes:
    if not banks:
        return b""
    items = [(b.bank_name, _to_float(b.balance) or 0) for b in banks if _to_float(b.balance)]
    if not items:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(max(7, len(items) * 1.8), 4.5))
    labels, vals = zip(*items)
    colors = [_BLUE if v >= 0 else _RED for v in vals]
    bars = ax.bar(labels, vals, color=colors, alpha=0.85, width=0.5)
    ax.set_title("Banka Bakiyeleri", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Bakiye")
    ax.grid(axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=30)
    for bar, v in zip(bars, vals):
        ax.annotate(_fmt(v), xy=(bar.get_x() + bar.get_width() / 2, v),
                    xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=9)
    fig.tight_layout()
    return _save_fig(fig)


# ── PDF üretici ───────────────────────────────────────────────────────────────

def generate_pdf_report(
    report,
    company,
    banks=None,
    collections=None,
    projects=None,
    investments=None,
    ai_ratios: Optional[dict] = None,
    ai_narrative: Optional[dict] = None,
    currency: str = "TRY",
) -> bytes:
    """
    Tüm finansal verileri, grafikleri ve AI yorumlarını içeren kapsamlı PDF raporu üretir.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
        Table, TableStyle, PageBreak, HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )
    W = A4[0] - 4 * cm

    BL  = HexColor(_BLUE)
    GR  = HexColor(_GREEN)
    RD  = HexColor(_RED)
    LBL = HexColor(_LBLUE)
    LGR = HexColor(_LGREEN)
    LG  = HexColor(_LGRAY)
    GY  = HexColor(_GRAY)

    base    = getSampleStyleSheet()
    s_cover = ParagraphStyle("Cover", parent=base["Title"],
                             fontName="Helvetica-Bold", fontSize=26,
                             textColor=BL, alignment=TA_CENTER, spaceAfter=8)
    s_sub   = ParagraphStyle("Sub",  parent=base["Normal"],
                             fontName="Helvetica", fontSize=12,
                             textColor=GY, alignment=TA_CENTER, spaceAfter=4)
    s_h1    = ParagraphStyle("H1",   parent=base["Heading1"],
                             fontName="Helvetica-Bold", fontSize=14,
                             textColor=BL, spaceBefore=14, spaceAfter=5)
    s_h2    = ParagraphStyle("H2",   parent=base["Heading2"],
                             fontName="Helvetica-Bold", fontSize=11,
                             textColor=GY, spaceBefore=8, spaceAfter=4)
    s_body  = ParagraphStyle("Body", parent=base["Normal"],
                             fontName="Helvetica", fontSize=10,
                             leading=16, spaceAfter=6, alignment=TA_JUSTIFY)
    s_small = ParagraphStyle("Small", parent=base["Normal"],
                             fontName="Helvetica", fontSize=8,
                             textColor=GY, spaceAfter=3)
    s_ctr   = ParagraphStyle("Ctr",  parent=base["Normal"],
                             fontName="Helvetica", fontSize=10, alignment=TA_CENTER)
    s_kpi   = ParagraphStyle("KPI",  parent=base["Normal"],
                             fontName="Helvetica-Bold", fontSize=18,
                             textColor=BL, alignment=TA_CENTER)
    s_ok    = ParagraphStyle("OK",   parent=base["Normal"],
                             fontName="Helvetica-Bold", fontSize=10,
                             textColor=GR, alignment=TA_LEFT, spaceAfter=3)
    s_warn  = ParagraphStyle("Warn", parent=base["Normal"],
                             fontName="Helvetica-Bold", fontSize=10,
                             textColor=RD, alignment=TA_LEFT, spaceAfter=3)

    story = []

    def _hr(color=_BLUE, thick=1.0):
        return HRFlowable(width="100%", thickness=thick,
                          color=HexColor(color), spaceAfter=6, spaceBefore=2)

    def _section(num: str, title: str):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"{num}. {title}", s_h1))
        story.append(_hr())

    def _embed_img(png_bytes: bytes, width=None):
        if not png_bytes:
            return None
        try:
            img = RLImage(io.BytesIO(png_bytes))
            target_w = width or W
            if img.imageWidth > 0:
                ratio = img.imageHeight / img.imageWidth
                img.drawWidth  = target_w
                img.drawHeight = target_w * ratio
            return img
        except Exception as exc:
            logger.warning("Görsel PDF'e eklenemedi: %s", exc)
            return None

    def _data_table(headers, rows, col_widths=None):
        if not rows:
            return None
        data = [headers] + rows
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0),  (-1, 0),   BL),
            ("TEXTCOLOR",    (0, 0),  (-1, 0),   white),
            ("FONTNAME",     (0, 0),  (-1, 0),   "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0),  (-1, -1),  9),
            ("ALIGN",        (0, 0),  (-1, -1),  "CENTER"),
            ("VALIGN",       (0, 0),  (-1, -1),  "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LBL, white]),
            ("GRID",         (0, 0),  (-1, -1),  0.4, HexColor("#B0BEC5")),
            ("TOPPADDING",   (0, 0),  (-1, -1),  4),
            ("BOTTOMPADDING",(0, 0),  (-1, -1),  4),
            ("LEFTPADDING",  (0, 0),  (-1, -1),  6),
            ("RIGHTPADDING", (0, 0),  (-1, -1),  6),
        ]))
        return t

    # ── KAPAK ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph(company.name, s_cover))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Kapsamlı Finansal Analiz Raporu", s_sub))
    period_str = (
        f"{report.fiscal_year}  |  "
        f"{report.period.value.upper()}  |  "
        f"{report.report_type.value.replace('_', ' ').title()}"
    )
    story.append(Paragraph(period_str, s_sub))
    story.append(Paragraph(
        f"Oluşturulma tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        s_small,
    ))
    story.append(_hr(thick=2))
    story.append(Spacer(1, 0.5 * cm))

    # KPI satırı
    score = (ai_ratios or {}).get("financial_score")
    ta    = _to_float(report.total_assets)
    rev   = _to_float(report.revenue)
    ni    = _to_float(report.net_income)
    eq    = _to_float(report.total_equity)

    kpi_cells = [
        Paragraph(
            f'<b>{_fmt(ta, currency)}</b><br/>'
            f'<font size="8" color="{_GRAY}">Toplam Varlık</font>', s_ctr
        ) if ta else Paragraph("—", s_ctr),
        Paragraph(
            f'<b>{_fmt(rev, currency)}</b><br/>'
            f'<font size="8" color="{_GRAY}">Gelir</font>', s_ctr
        ) if rev else Paragraph("—", s_ctr),
        Paragraph(
            f'<b>{_fmt(ni, currency)}</b><br/>'
            f'<font size="8" color="{_GRAY}">Net Kâr</font>', s_ctr
        ) if ni else Paragraph("—", s_ctr),
        Paragraph(
            f'<b>{score}/100</b><br/>'
            f'<font size="8" color="{_GRAY}">AI Skoru</font>', s_ctr
        ) if score else Paragraph("—", s_ctr),
    ]
    kpi_t = Table([kpi_cells], colWidths=[W / 4] * 4)
    kpi_t.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 1,   BL),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, HexColor("#B0BEC5")),
        ("BACKGROUND",   (0, 0), (-1, -1), LBL),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(kpi_t)
    story.append(PageBreak())

    # ── 1. YÖNETİCİ ÖZETİ ────────────────────────────────────────────────────
    _section("1", "Yönetici Özeti")

    if ai_narrative and ai_narrative.get("executive_summary"):
        story.append(Paragraph(ai_narrative["executive_summary"], s_body))
    else:
        parts = []
        if ta:  parts.append(f"Toplam varlık büyüklüğü <b>{_fmt(ta, currency)}</b>.")
        if rev: parts.append(f"Dönem geliri <b>{_fmt(rev, currency)}</b>.")
        if ni:  parts.append(f"Net kâr <b>{_fmt(ni, currency)}</b>.")
        if eq:  parts.append(f"Özkaynak <b>{_fmt(eq, currency)}</b>.")
        if parts:
            story.append(Paragraph(" ".join(parts), s_body))

    if ai_narrative:
        strengths = ai_narrative.get("key_strengths", [])
        risks     = ai_narrative.get("key_risks", [])
        if strengths or risks:
            story.append(Spacer(1, 8))
            max_len = max(len(strengths), len(risks), 1)
            sr_rows = []
            for i in range(max_len):
                s_p = Paragraph(f"✓  {strengths[i]}", s_ok)   if i < len(strengths) else Paragraph("", s_body)
                r_p = Paragraph(f"⚠  {risks[i]}", s_warn)     if i < len(risks)     else Paragraph("", s_body)
                sr_rows.append([s_p, r_p])
            sr_t = Table(
                [[Paragraph("<b>Güçlü Yönler</b>", s_h2),
                  Paragraph("<b>Risk Faktörleri</b>", s_h2)]] + sr_rows,
                colWidths=[W / 2, W / 2],
            )
            sr_t.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (0, 0),  LGR),
                ("BACKGROUND",   (1, 0), (1, 0),  HexColor("#FFEBEE")),
                ("GRID",         (0, 0), (-1, -1), 0.3, HexColor("#B0BEC5")),
                ("TOPPADDING",   (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
                ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(sr_t)

    # ── 2. BİLANÇO ───────────────────────────────────────────────────────────
    story.append(PageBreak())
    _section("2", "Bilanço Analizi")

    if ai_narrative and ai_narrative.get("balance_sheet_commentary"):
        story.append(Paragraph(ai_narrative["balance_sheet_commentary"], s_body))

    bs_fields = [
        ("Nakit ve Eşdeğerleri",         report.cash_and_equivalents),
        ("Kısa Vadeli Yatırımlar",        report.short_term_investments),
        ("Ticari Alacaklar",              report.accounts_receivable),
        ("Stoklar",                       report.inventory),
        ("Diğer Dönen Varlıklar",         report.other_current_assets),
        ("TOPLAM DÖNEN VARLIK",           report.total_current_assets),
        ("Maddi Duran Varlıklar",         report.property_plant_equipment),
        ("Maddi Olmayan Duran Varlıklar", report.intangible_assets),
        ("Uzun Vadeli Yatırımlar",        report.long_term_investments),
        ("TOPLAM DURAN VARLIK",           report.total_non_current_assets),
        ("TOPLAM VARLIK",                 report.total_assets),
        ("Ticari Borçlar",                report.accounts_payable),
        ("Kısa Vadeli Borçlar",           report.short_term_debt),
        ("TOPLAM KISA V. YÜKÜMLÜLÜK",     report.total_current_liabilities),
        ("Uzun Vadeli Borçlar",           report.long_term_debt),
        ("TOPLAM UZUN V. YÜKÜMLÜLÜK",     report.total_non_current_liabilities),
        ("TOPLAM BORÇ",                   report.total_liabilities),
        ("Ödenmiş Sermaye",               report.share_capital),
        ("Dağıtılmamış Kârlar",           report.retained_earnings),
        ("TOPLAM ÖZKAYNAK",               report.total_equity),
    ]
    bs_rows = [[l, _fmt(_to_float(v), currency)]
               for l, v in bs_fields if _to_float(v) is not None]
    t = _data_table(["Bilanço Kalemi", "Tutar"], bs_rows, [W * 0.70, W * 0.30])
    if t:
        story.append(t)

    story.append(Spacer(1, 10))
    img = _embed_img(_chart_asset_pie(report), width=W * 0.50)
    if img:
        story.append(img)
    img = _embed_img(_chart_balance_structure(report), width=W)
    if img:
        story.append(img)

    # ── 3. GELİR TABLOSU ─────────────────────────────────────────────────────
    story.append(PageBreak())
    _section("3", "Gelir Tablosu Analizi")

    if ai_narrative and ai_narrative.get("income_commentary"):
        story.append(Paragraph(ai_narrative["income_commentary"], s_body))

    inc_fields = [
        ("Gelir",                  report.revenue),
        ("Satılan Malın Maliyeti", report.cost_of_goods_sold),
        ("BRÜT KÂR",               report.gross_profit),
        ("Faaliyet Giderleri",      report.operating_expenses),
        ("EBITDA",                 report.ebitda),
        ("EBIT",                   report.ebit),
        ("Faiz Gideri",             report.interest_expense),
        ("Vergi Öncesi Kâr",        report.income_before_tax),
        ("Vergi",                  report.income_tax),
        ("NET KÂR",                report.net_income),
    ]
    inc_rows = [[l, _fmt(_to_float(v), currency)]
                for l, v in inc_fields if _to_float(v) is not None]
    t = _data_table(["Gelir Tablosu Kalemi", "Tutar"], inc_rows, [W * 0.70, W * 0.30])
    if t:
        story.append(t)

    img = _embed_img(_chart_income_bar(report), width=W)
    if img:
        story.append(Spacer(1, 8))
        story.append(img)

    # ── 4. NAKİT AKIŞI ───────────────────────────────────────────────────────
    story.append(PageBreak())
    _section("4", "Nakit Akış Analizi")

    if ai_narrative and ai_narrative.get("cashflow_commentary"):
        story.append(Paragraph(ai_narrative["cashflow_commentary"], s_body))

    cf_fields = [
        ("İşletme Faaliyetleri Nakit Akışı",    report.operating_cash_flow),
        ("Yatırım Faaliyetleri Nakit Akışı",     report.investing_cash_flow),
        ("Finansman Faaliyetleri Nakit Akışı",   report.financing_cash_flow),
        ("Serbest Nakit Akışı",                  report.free_cash_flow),
        ("Net Nakit Değişimi",                   report.net_change_in_cash),
    ]
    cf_rows = [[l, _fmt(_to_float(v), currency)]
               for l, v in cf_fields if _to_float(v) is not None]
    t = _data_table(["Nakit Akış Kalemi", "Tutar"], cf_rows, [W * 0.70, W * 0.30])
    if t:
        story.append(t)

    img = _embed_img(_chart_cashflow(report), width=W)
    if img:
        story.append(Spacer(1, 8))
        story.append(img)

    # ── 5. FİNANSAL ORANLAR ──────────────────────────────────────────────────
    if ai_ratios:
        story.append(PageBreak())
        _section("5", "Finansal Oran Analizi")

        if ai_narrative and ai_narrative.get("ratio_commentary"):
            story.append(Paragraph(ai_narrative["ratio_commentary"], s_body))

        def _r(v):
            if v is None:
                return "—"
            try:
                return f"{float(v):.2f}"
            except (TypeError, ValueError):
                return str(v)

        liq  = ai_ratios.get("liquidity", {})
        lev  = ai_ratios.get("leverage", {})
        prof = ai_ratios.get("profitability", {})
        eff  = ai_ratios.get("efficiency", {})

        ratio_rows = []
        if liq:
            ratio_rows += [
                ["Cari Oran",    _r(liq.get("current_ratio")),  "Likidite"],
                ["Hızlı Oran",   _r(liq.get("quick_ratio")),    "Likidite"],
                ["Nakit Oranı",  _r(liq.get("cash_ratio")),     "Likidite"],
            ]
        if lev:
            ratio_rows += [
                ["Borç/Özkaynak",    _r(lev.get("debt_to_equity")),    "Kaldıraç"],
                ["Borç/Varlık",      _r(lev.get("debt_to_assets")),    "Kaldıraç"],
                ["Faiz Karşılama",   _r(lev.get("interest_coverage")), "Kaldıraç"],
            ]
        if prof:
            ratio_rows += [
                ["Brüt Kâr Marjı",  _r(prof.get("gross_margin")),  "Kârlılık"],
                ["Net Kâr Marjı",   _r(prof.get("net_margin")),    "Kârlılık"],
                ["EBITDA Marjı",    _r(prof.get("ebitda_margin")), "Kârlılık"],
                ["ROA",             _r(prof.get("roa")),           "Kârlılık"],
                ["ROE",             _r(prof.get("roe")),           "Kârlılık"],
            ]
        if eff:
            ratio_rows += [
                ["Varlık Devir Hızı",  _r(eff.get("asset_turnover")),       "Verimlilik"],
                ["Alacak Devir Hızı",  _r(eff.get("receivables_turnover")), "Verimlilik"],
                ["Stok Devir Hızı",    _r(eff.get("inventory_turnover")),   "Verimlilik"],
            ]

        t = _data_table(
            ["Oran", "Değer", "Kategori"],
            ratio_rows,
            [W * 0.50, W * 0.25, W * 0.25],
        )
        if t:
            story.append(t)

        img = _embed_img(_chart_ratio_radar(ai_ratios), width=W * 0.55)
        if img:
            story.append(Spacer(1, 8))
            story.append(img)

        overall = ai_ratios.get("overall_assessment")
        if overall:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Genel Değerlendirme</b>", s_h2))
            story.append(Paragraph(overall, s_body))

        score_val = ai_ratios.get("financial_score")
        if score_val:
            story.append(Paragraph(
                f"Finansal Sağlık Skoru: <b>{score_val} / 100</b>", s_kpi,
            ))

    # ── 6. GENİŞLETİLMİŞ VERİLER ─────────────────────────────────────────────
    has_ext = any([banks, collections, projects, investments])
    if has_ext:
        story.append(PageBreak())
        _section("6", "Genişletilmiş Finansal Veriler")

        if banks:
            story.append(Paragraph("Banka Hesapları", s_h2))
            bank_rows = [
                [b.bank_name, b.currency,
                 _fmt(_to_float(b.balance), b.currency),
                 _fmt(_to_float(b.credit_limit), b.currency),
                 _fmt(_to_float(b.credit_usage), b.currency)]
                for b in banks
            ]
            t = _data_table(
                ["Banka", "Para Birimi", "Bakiye", "Kredi Limiti", "Kullanılan"],
                bank_rows,
                [W*0.28, W*0.12, W*0.20, W*0.20, W*0.20],
            )
            if t:
                story.append(t)
            img = _embed_img(_chart_bank_balances(banks), width=W)
            if img:
                story.append(Spacer(1, 6))
                story.append(img)

        if collections:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Tahsilat Durumu", s_h2))
            col_rows = [
                [c.counterparty or "—",
                 c.collection_type.value,
                 _fmt(_to_float(c.amount), currency),
                 str(c.due_date) if c.due_date else "—",
                 "Evet" if c.is_overdue else "Hayır"]
                for c in collections
            ]
            t = _data_table(
                ["Karşı Taraf", "Tür", "Tutar", "Vade", "Gecikmiş"],
                col_rows,
                [W*0.30, W*0.15, W*0.20, W*0.20, W*0.15],
            )
            if t:
                story.append(t)
            img = _embed_img(_chart_collections(collections), width=W * 0.55)
            if img:
                story.append(Spacer(1, 6))
                story.append(img)

        if projects:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Projeler", s_h2))
            proj_rows = [
                [p.name, p.client_name or "—", p.status.value,
                 _fmt(_to_float(p.value), currency) if p.value else "—",
                 str(p.end_date) if p.end_date else "—"]
                for p in projects
            ]
            t = _data_table(
                ["Proje Adı", "Müşteri", "Durum", "Değer", "Bitiş"],
                proj_rows,
                [W*0.28, W*0.22, W*0.15, W*0.20, W*0.15],
            )
            if t:
                story.append(t)

        if investments:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Yatırım Portföyü", s_h2))
            inv_rows = [
                [inv.name, inv.sector or inv.investment_type or "—",
                 inv.status.value,
                 _fmt(_to_float(inv.purchase_value), currency) if inv.purchase_value else "—",
                 _fmt(_to_float(inv.current_value),  currency) if inv.current_value  else "—"]
                for inv in investments
            ]
            t = _data_table(
                ["Yatırım Adı", "Sektör", "Durum", "Alış Değeri", "Güncel Değer"],
                inv_rows,
                [W*0.28, W*0.22, W*0.15, W*0.18, W*0.17],
            )
            if t:
                story.append(t)
            img = _embed_img(_chart_investments(investments), width=W * 0.55)
            if img:
                story.append(Spacer(1, 6))
                story.append(img)

    # ── 7. SONUÇ VE ÖNERİLER ─────────────────────────────────────────────────
    story.append(PageBreak())
    _section("7", "Sonuç ve Öneriler")

    if ai_narrative:
        if ai_narrative.get("overall_conclusion"):
            story.append(Paragraph(ai_narrative["overall_conclusion"], s_body))
        recs = ai_narrative.get("recommendations", [])
        if recs:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Öneriler</b>", s_h2))
            for i, rec in enumerate(recs, 1):
                story.append(Paragraph(f"{i}.  {rec}", s_body))
    elif ai_ratios:
        pos   = ai_ratios.get("positive_indicators", [])
        risks = ai_ratios.get("risk_indicators", [])
        if pos:
            story.append(Paragraph("<b>Olumlu Göstergeler</b>", s_h2))
            for p in pos:
                story.append(Paragraph(f"•  {p}", s_body))
        if risks:
            story.append(Paragraph("<b>Risk Göstergeleri</b>", s_h2))
            for r in risks:
                story.append(Paragraph(f"•  {r}", s_body))

    # alt bilgi
    story.append(Spacer(1, cm))
    story.append(_hr(_GRAY, 0.5))
    story.append(Paragraph(
        f"Bu rapor {datetime.now().strftime('%d.%m.%Y')} tarihinde yapay zeka destekli "
        "finansal analiz platformu tarafından otomatik olarak oluşturulmuştur.",
        s_small,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
