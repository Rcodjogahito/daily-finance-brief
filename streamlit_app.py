"""Daily Finance Brief — Streamlit main page."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.archiver import list_brief_dates, list_alert_dates, load_brief, load_alerts


def _build_bloomberg_csv(news: list[dict], date: str) -> bytes:
    """Build Bloomberg-compatible CSV for deal flow tracking."""
    import io, csv
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "Date", "Rank", "Category", "Headline", "Source",
        "Sector", "Geography", "Deal_Size_Bn_EUR", "Confidence",
        "Source_Count", "URL", "Summary",
    ])
    for item in news:
        deal = item.get("deal_size_eur")
        deal_bn = f"{deal/1e9:.2f}" if deal else ""
        writer.writerow([
            item.get("date", date),
            item.get("rank", ""),
            item.get("category", ""),
            item.get("headline", ""),
            item.get("source", ""),
            item.get("sector", ""),
            item.get("geography", ""),
            deal_bn,
            item.get("confidence", ""),
            item.get("source_count", 1),
            item.get("url", ""),
            item.get("summary", "")[:200].replace("\n", " "),
        ])
    return buf.getvalue().encode("utf-8-sig")  # utf-8-sig = BOM for Excel/Bloomberg

st.set_page_config(
    page_title="Daily Finance Brief",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Optional password protection
_pwd = st.secrets.get("DASHBOARD_PASSWORD", "") if hasattr(st, "secrets") else ""
if _pwd:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔐 Daily Finance Brief")
            pwd = st.text_input("Mot de passe", type="password")
            if st.button("Connexion"):
                if pwd == _pwd:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────
st.sidebar.image("https://img.shields.io/badge/Daily%20Finance%20Brief-Coffee%20Economics%20News-0A1F44?style=for-the-badge", use_container_width=True)
st.sidebar.markdown("---")

dates = list_brief_dates()
alert_dates = list_alert_dates()

st.sidebar.markdown("### Navigation")
st.sidebar.page_link("streamlit_app.py", label="📊 Brief du jour", icon="📊")
st.sidebar.page_link("pages/1_📅_Historique.py", label="📅 Historique", icon="📅")
st.sidebar.page_link("pages/2_🔥_Alertes.py", label="🔥 Alertes chaudes", icon="🔥")
st.sidebar.page_link("pages/3_🌍_Heatmap.py", label="🌍 Heatmap deals", icon="🌍")
st.sidebar.page_link("pages/4_🔍_Recherche.py", label="🔍 Recherche", icon="🔍")
st.sidebar.markdown("---")

# Stats sidebar
total_briefs = len(dates)
total_alerts = sum(
    len((load_alerts(d) or {}).get("alerts", []))
    for d in alert_dates[:30]
)
last_update = dates[0] if dates else "—"
st.sidebar.metric("Briefs archivés", total_briefs)
st.sidebar.metric("Alertes (30j)", total_alerts)
st.sidebar.metric("Dernière MAJ", last_update)

# ── Main content ───────────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "M&A": "#16A34A", "LevFin": "#EA580C", "Energy": "#7C3AED",
    "Credit": "#2563EB", "Macro": "#475569", "Geo": "#DC2626",
    "Reg": "#CA8A04", "Sector": "#0891B2",
}

def category_badge(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#64748b")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700">{cat}</span>'


def render_news_card(item: dict) -> None:
    deal = f" &nbsp; **{item['deal_size_eur']/1e9:.1f} Md€**" if item.get("deal_size_eur") else ""
    confidence_badge = " ⚠️ *à vérifier*" if item.get("confidence") == "medium" else ""
    multi = f" ✓ {item['source_count']} sources" if item.get("source_count", 1) >= 2 else ""

    with st.container():
        col_rank, col_content = st.columns([1, 11])
        with col_rank:
            st.markdown(f"<div style='font-size:28px;font-weight:900;color:#0A1F44;padding-top:4px'>#{item.get('rank','')}</div>", unsafe_allow_html=True)
        with col_content:
            st.markdown(
                f"{category_badge(item.get('category','Sector'))}{deal}{confidence_badge}<span style='color:#16A34A;font-size:12px'>{multi}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"#### [{item.get('headline', item.get('title',''))}]({item.get('url','')})")
            st.caption(f"📰 {item.get('source','')} &nbsp; 🗓 {item.get('date','')} &nbsp; 📍 {item.get('geography','')} &nbsp; 🏭 {item.get('sector','')}")
            st.markdown(item.get("summary", ""))
            st.info(f"💡 **So what** — {item.get('so_what', '')}")
        st.markdown("---")


# ── Date selector ─────────────────────────────────────────────────────────
st.title("📊 Daily Finance Brief")

if not dates:
    st.warning("Aucun brief disponible. Le premier brief sera disponible après la prochaine exécution automatique.")
    st.stop()

selected_date = st.selectbox(
    "Sélectionner une date",
    options=dates,
    index=0,
    format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
)

brief = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news = brief.get("news", [])
stats = brief.get("stats", {})
market = brief.get("market_snapshot", {})

# ── Market snapshot bar ────────────────────────────────────────────────────
if market:
    st.markdown("#### 📈 Marchés")
    mkt_items = list(market.items())
    cols = st.columns(len(mkt_items))
    TREND_COLORS = {"up": "#16a34a", "down": "#dc2626", "flat": "#64748b"}
    for col, (label, data) in zip(cols, mkt_items):
        val = data.get("value", "—")
        unit = data.get("unit", "")
        change = data.get("change", "")
        trend = data.get("trend", "flat")
        color = TREND_COLORS.get(trend, "#64748b")
        col.markdown(
            f"**{label}**  \n"
            f"<span style='font-size:18px;font-weight:700'>{val}{' ' + unit if unit else ''}</span>  \n"
            f"<span style='color:{color};font-size:13px'>{change or '—'}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("---")

# Stats bar
col1, col2, col3, col4 = st.columns(4)
col1.metric("News collectées", stats.get("collected", "—"))
col2.metric("Après filtrage", stats.get("filtered", "—"))
col3.metric("Sélectionnées", stats.get("post_verified", len(news)))
col4.metric("Généré à", brief.get("generated_at", "")[:16].replace("T", " "))

if brief.get("low_volume"):
    st.warning("⚠️ Volume faible aujourd'hui — seules les news les plus pertinentes sont incluses.")

st.markdown("---")

# Category filter
cats = sorted({item.get("category", "Sector") for item in news})
selected_cats = st.multiselect("Filtrer par catégorie", cats, default=cats, key="main_cat_filter")
filtered_news = [n for n in news if n.get("category", "Sector") in selected_cats]

# Render cards
for item in filtered_news:
    render_news_card(item)

# ── PDF Export ─────────────────────────────────────────────────────────────
st.markdown("---")
col_pdf, col_info = st.columns([2, 3])
with col_pdf:
    if st.button("📥 Export PDF du brief", type="primary"):
        try:
            from xhtml2pdf import pisa
            from jinja2 import Environment, FileSystemLoader

            template_dir = Path(__file__).parent / "src" / "templates"
            env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
            template = env.get_template("email_brief.html")
            html = template.render(
                brief=brief,
                streamlit_url=st.secrets.get("STREAMLIT_URL", "") if hasattr(st, "secrets") else "",
                generated_at=datetime.now().strftime("%d/%m/%Y à %H:%M"),
            )
            import io
            pdf_buf = io.BytesIO()
            pisa.CreatePDF(html, dest=pdf_buf)
            pdf_bytes = pdf_buf.getvalue()
            st.download_button(
                "⬇️ Télécharger le PDF",
                data=pdf_bytes,
                file_name=f"brief_{selected_date}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Erreur PDF: {e}")
with col_info:
    st.caption(f"Brief du {selected_date} • {len(news)} news • {stats.get('collected', '?')} sources scannées")

# ── Bloomberg CSV Export ────────────────────────────────────────────────────
if news:
    bloomberg_csv = _build_bloomberg_csv(news, selected_date)
    st.download_button(
        "📊 Export Bloomberg CSV",
        data=bloomberg_csv,
        file_name=f"bloomberg_brief_{selected_date}.csv",
        mime="text/csv",
        help="Format compatible Bloomberg Terminal import (deal flow tracker)",
    )
