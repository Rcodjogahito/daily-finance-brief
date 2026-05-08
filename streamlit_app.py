"""Daily Finance Brief — Streamlit main page."""
import io as _io
import csv as _csv
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.archiver import list_brief_dates, list_alert_dates, load_brief, load_alerts
from src.enrichment import REGION_GEO_MAP
from src.styles import inject_css, sidebar_brand, page_toolbar, news_card, CATEGORY_COLORS, CATEGORY_LABELS, ALL_CATEGORIES


_ALL_REGIONS = ["Europe", "EMEA", "APAC", "Afrique", "Amériques", "Global"]


def _geos_for_regions(selected_regions: list[str]) -> set[str]:
    """Return the set of geographies that fall within any of the selected regions."""
    geos: set[str] = set()
    for r in selected_regions:
        geos |= REGION_GEO_MAP.get(r, set())
    return geos


def _build_bloomberg_csv(news: list[dict], date: str) -> bytes:
    buf = _io.StringIO()
    writer = _csv.writer(buf, quoting=_csv.QUOTE_ALL)
    writer.writerow([
        "Date", "Rank", "Category", "Headline", "Source",
        "Sector", "Geography", "Region", "Deal_Size_Bn_EUR", "Confidence",
        "Source_Count", "URL", "Summary",
    ])
    for item in news:
        deal = item.get("deal_size_eur")
        writer.writerow([
            item.get("date", date), item.get("rank", ""),
            item.get("category", ""), item.get("headline", ""),
            item.get("source", ""), item.get("sector", ""),
            item.get("geography", ""), item.get("region", ""),
            f"{deal/1e9:.2f}" if deal else "",
            item.get("confidence", ""), item.get("source_count", 1),
            item.get("url", ""), item.get("summary", "")[:200].replace("\n", " "),
        ])
    return buf.getvalue().encode("utf-8-sig")


st.set_page_config(
    page_title="Daily Finance Brief — Coffee Economics News",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Auth (optional) ────────────────────────────────────────────────────────
_pwd = st.secrets.get("DASHBOARD_PASSWORD", "") if hasattr(st, "secrets") else ""
if _pwd:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown("### Daily Finance Brief")
            pwd = st.text_input("Mot de passe", type="password")
            if st.button("Connexion"):
                if pwd == _pwd:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────
sidebar_brand()
st.sidebar.markdown("---")

dates       = list_brief_dates()
alert_dates = list_alert_dates()

st.sidebar.markdown("### Navigation")
st.sidebar.page_link("streamlit_app.py",              label="Brief du jour")
st.sidebar.page_link("pages/1_📅_Historique.py",     label="Historique")
st.sidebar.page_link("pages/2_🔥_Alertes.py",        label="Alertes")
st.sidebar.page_link("pages/3_🌍_Heatmap.py",        label="Heatmap deals")
st.sidebar.page_link("pages/4_🔍_Recherche.py",      label="Recherche")
st.sidebar.page_link("pages/5_📧_Abonnement.py",     label="Abonnement email")
st.sidebar.markdown("---")

total_alerts = sum(
    len((load_alerts(d) or {}).get("alerts", []))
    for d in alert_dates[:30]
)
st.sidebar.metric("Briefs archivés", len(dates))
st.sidebar.metric("Alertes (30 j)", total_alerts)
st.sidebar.metric("Dernière MAJ", dates[0] if dates else "—")

# ── Header ─────────────────────────────────────────────────────────────────
page_toolbar()

# Handle subscription query param (?page=abonnement)
_qp = st.query_params
if _qp.get("page") == "abonnement":
    st.switch_page("pages/5_📧_Abonnement.py")

st.markdown(
    '<div style="margin-bottom:4px">'
    '<span style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF">Coffee Economics News</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.title("Daily Finance Brief")

if not dates:
    st.warning("Aucun brief disponible. Le premier sera généré à 08h30.")
    st.stop()

selected_date = st.selectbox(
    "Date",
    options=dates,
    index=0,
    format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
)

brief  = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news   = brief.get("news", [])
stats  = brief.get("stats", {})
market = brief.get("market_snapshot", {})

st.markdown("---")

# ── Market snapshot ────────────────────────────────────────────────────────
if market:
    st.markdown(
        '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:12px">Marchés</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(market))
    TREND = {"up": "#059669", "down": "#C0392B", "flat": "#9CA3AF"}
    ARROW = {"up": "▲", "down": "▼", "flat": ""}
    for col, (label, data) in zip(cols, market.items()):
        trend  = data.get("trend", "flat")
        color  = TREND.get(trend, "#9CA3AF")
        arrow  = ARROW.get(trend, "")
        change = data.get("change", "")
        unit   = f' <span style="font-size:11px;color:#9CA3AF">{data["unit"]}</span>' if data.get("unit") else ""
        col.markdown(
            f'<div style="padding:2px 0">'
            f'<div style="font-size:9px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">{label}</div>'
            f'<div style="font-size:19px;font-weight:700;color:#0B1D2E;letter-spacing:-0.5px;line-height:1">{data.get("value","—")}{unit}</div>'
            f'<div style="font-size:11px;font-weight:500;color:{color};margin-top:3px">{arrow} {change or "—"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")

st.caption(f"Généré le {brief.get('generated_at', '')[:10]} à {brief.get('generated_at', '')[11:16]}")

if brief.get("low_volume"):
    st.warning("Volume réduit — seules les news les plus pertinentes ont été retenues.")

st.markdown("---")

# ── Filters ────────────────────────────────────────────────────────────────
fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    st.markdown(
        '<div style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Région</div>',
        unsafe_allow_html=True,
    )
    selected_regions = st.multiselect(
        "Région", _ALL_REGIONS, default=_ALL_REGIONS, key="main_region", label_visibility="collapsed",
    )

with fcol2:
    st.markdown(
        '<div style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Type d\'information</div>',
        unsafe_allow_html=True,
    )
    cats_present  = sorted({item.get("category", "Sector") for item in news})
    cat_options   = {CATEGORY_LABELS.get(c, c): c for c in cats_present}
    selected_labels = st.multiselect(
        "Type", list(cat_options.keys()), default=list(cat_options.keys()), key="main_cat", label_visibility="collapsed",
    )
    selected_cats = [cat_options[l] for l in selected_labels]

with fcol3:
    st.markdown(
        '<div style="font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Secteur</div>',
        unsafe_allow_html=True,
    )
    sectors_present = sorted({item.get("sector", "Other") for item in news})
    selected_sectors = st.multiselect(
        "Secteur", sectors_present, default=sectors_present, key="main_sector", label_visibility="collapsed",
    )

# Apply filters
allowed_geos = _geos_for_regions(selected_regions) if selected_regions else set()
filtered_news = [
    n for n in news
    if n.get("category", "Sector") in selected_cats
    and n.get("sector", "Other") in selected_sectors
    and (not selected_regions or n.get("geography", "Global") in allowed_geos)
]

st.markdown(
    f'<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin:8px 0 12px">{len(filtered_news)} news affichées</div>',
    unsafe_allow_html=True,
)

# ── News cards ─────────────────────────────────────────────────────────────
for item in filtered_news:
    news_card(item)

# ── Exports ────────────────────────────────────────────────────────────────
st.markdown("---")
col_pdf, col_csv, col_info = st.columns([1, 1, 2])

with col_pdf:
    if st.button("Export PDF"):
        try:
            from xhtml2pdf import pisa
            from jinja2 import Environment, FileSystemLoader

            template_dir = Path(__file__).parent / "src" / "templates"
            env  = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
            html = env.get_template("email_brief.html").render(
                brief=brief,
                streamlit_url=st.secrets.get("STREAMLIT_URL", "") if hasattr(st, "secrets") else "",
                generated_at=datetime.now().strftime("%d/%m/%Y à %H:%M"),
            )
            pdf_buf = _io.BytesIO()
            pisa.CreatePDF(html, dest=pdf_buf)
            st.download_button(
                "Télécharger le PDF",
                data=pdf_buf.getvalue(),
                file_name=f"brief_{selected_date}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Erreur PDF : {e}")

with col_csv:
    if news:
        st.download_button(
            "Export Bloomberg CSV",
            data=_build_bloomberg_csv(news, selected_date),
            file_name=f"bloomberg_{selected_date}.csv",
            mime="text/csv",
            help="Format compatible Bloomberg Terminal / Excel deal tracker",
        )

with col_info:
    st.caption(
        f"Brief du {selected_date} · {len(news)} news · "
        f"{stats.get('collected', '?')} sources scannées"
    )
