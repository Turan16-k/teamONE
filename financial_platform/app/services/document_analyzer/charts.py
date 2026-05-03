"""
Grafik üretici — matplotlib ile PNG baytları üretir.
Her fonksiyon bağımsız çalışır; eksik veri varsa boş bytes döner.
"""
from __future__ import annotations
import io
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_PALETTE = ["#1565C0", "#4CAF50", "#FF5722", "#9C27B0", "#FF9800", "#00BCD4", "#795548"]
_FIG_W, _FIG_H, _DPI = 11, 6, 110


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _num(v: Any) -> float:
    try:
        return float(str(v).replace(",", "").replace(" ", "").replace("₺", ""))
    except (ValueError, TypeError):
        return 0.0


def _fmt(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"{v/1_000:.0f}K"
    return f"{v:.0f}"


def _save(fig) -> bytes:
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ── grafik fonksiyonları ──────────────────────────────────────────────────────

def revenue_expense_bar(data: dict) -> bytes:
    labels   = data.get("labels", [])
    revenues = [_num(v) for v in data.get("revenue", [])]
    expenses = [_num(v) for v in data.get("expenses", [])]
    if not labels:
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    x, w = range(len(labels)), 0.38
    b1 = ax.bar([i - w / 2 for i in x], revenues, w, label="Gelir",  color="#4CAF50", alpha=0.88)
    b2 = ax.bar([i + w / 2 for i in x], expenses, w, label="Gider", color="#FF5722", alpha=0.88)
    ax.set_title("Gelir ve Gider Karşılaştırması", fontsize=14, fontweight="bold", pad=14)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_ylabel("Tutar"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        if h:
            ax.annotate(_fmt(h), xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    fig.tight_layout()
    return _save(fig)


def category_pie(data: dict) -> bytes:
    labels = data.get("labels", [])
    values = [_num(v) for v in data.get("values", [])]
    pairs  = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not pairs:
        return b""
    lbls, vals = zip(*pairs)
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 7))
    wedges, texts, auto = ax.pie(
        vals, labels=lbls, colors=_PALETTE[: len(vals)],
        autopct="%1.1f%%", startangle=90, pctdistance=0.80, labeldistance=1.14,
    )
    for t in auto:
        t.set_fontsize(9)
    ax.set_title("Kategori Dağılımı", fontsize=14, fontweight="bold", pad=18)
    fig.tight_layout()
    return _save(fig)


def monthly_trend_line(data: dict) -> bytes:
    months = data.get("months", [])
    values = [_num(v) for v in data.get("values", [])]
    if not months or not any(values):
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    ax.plot(months, values, marker="o", linewidth=2.5, markersize=7,
            color="#1565C0", markerfacecolor="white", markeredgewidth=2.2)
    ax.fill_between(months, values, alpha=0.10, color="#1565C0")
    ax.set_title("Aylık Trend Analizi", fontsize=14, fontweight="bold", pad=14)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=40, ha="right")
    ax.set_ylabel("Tutar"); ax.grid(alpha=0.3)
    for x, y in zip(range(len(months)), values):
        ax.annotate(_fmt(y), xy=(x, y), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8)
    fig.tight_layout()
    return _save(fig)


def asset_structure_bar(data: dict) -> bytes:
    labels = data.get("labels", [])
    values = [_num(v) for v in data.get("values", [])]
    pairs  = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not pairs:
        return b""
    lbls, vals = zip(*pairs)
    plt = _plt()
    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    bars = ax.barh(lbls, vals, color=_PALETTE[: len(vals)], alpha=0.88)
    ax.set_title("Varlık ve Kaynak Yapısı", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Tutar"); ax.grid(axis="x", alpha=0.3)
    for bar in bars:
        w = bar.get_width()
        ax.annotate(_fmt(w), xy=(w, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points", va="center", fontsize=9)
    fig.tight_layout()
    return _save(fig)


def cash_flow_bar(data: dict) -> bytes:
    cats   = data.get("categories", ["İşletme", "Yatırım", "Finansman"])
    values = [_num(v) for v in data.get("values", [])]
    if not any(values):
        return b""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#4CAF50" if v >= 0 else "#FF5722" for v in values]
    bars = ax.bar(cats, values, color=colors, alpha=0.88, width=0.5)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_title("Nakit Akış Analizi", fontsize=14, fontweight="bold", pad=14)
    ax.set_ylabel("Tutar"); ax.grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, values):
        ax.annotate(_fmt(v), xy=(bar.get_x() + bar.get_width() / 2, v),
                    xytext=(0, 6 if v >= 0 else -14), textcoords="offset points",
                    ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    return _save(fig)


def ratio_radar(ratios: dict) -> bytes:
    """Finansal oran örümcek grafiği (enterprise)."""
    clean = {k: _num(v) for k, v in ratios.items() if v is not None and _num(v) > 0}
    if len(clean) < 3:
        return b""
    import numpy as np
    plt = _plt()
    labels = list(clean.keys())
    values = list(clean.values())
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]; values += values[:1]; labels += labels[:1]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.plot(angles, values, "o-", linewidth=2, color="#1565C0")
    ax.fill(angles, values, alpha=0.20, color="#1565C0")
    ax.set_thetagrids(np.degrees(angles[:-1]), labels[:-1], fontsize=10)
    ax.set_title("Finansal Oran Analizi", fontsize=13, fontweight="bold", pad=20)
    fig.tight_layout()
    return _save(fig)


# ── orkestrasyon ──────────────────────────────────────────────────────────────

class ChartGenerator:
    def generate(self, chart_data: dict, tier: str, ratio_data: dict | None = None) -> Dict[str, bytes]:
        out: Dict[str, bytes] = {}
        try:
            rd = chart_data.get("revenue_expense", {})
            if rd.get("labels"):
                b = revenue_expense_bar(rd)
                if b: out["gelir_gider.png"] = b

            cd = chart_data.get("category_breakdown", {})
            if cd.get("labels"):
                b = category_pie(cd)
                if b: out["kategori_dagilim.png"] = b

            td = chart_data.get("monthly_trend", {})
            if td.get("months"):
                b = monthly_trend_line(td)
                if b: out["aylik_trend.png"] = b

            if tier == "enterprise":
                ad = chart_data.get("asset_structure", {})
                if ad.get("labels"):
                    b = asset_structure_bar(ad)
                    if b: out["varlik_yapisi.png"] = b

                cf = chart_data.get("cash_flow", {})
                if cf.get("values"):
                    b = cash_flow_bar(cf)
                    if b: out["nakit_akisi.png"] = b

                if ratio_data:
                    b = ratio_radar(ratio_data)
                    if b: out["oran_radar.png"] = b

        except ImportError:
            logger.warning("matplotlib kurulu değil — grafikler atlandı")
        except Exception as exc:
            logger.error("Grafik oluşturma hatası: %s", exc)

        return out
