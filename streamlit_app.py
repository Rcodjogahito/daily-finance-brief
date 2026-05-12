"""Daily Finance Brief — Streamlit main page."""
import io as _io
import csv as _csv
from datetime import datetime

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
    '<div style="margin-bottom:5px">'
    '<span style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C">Coffee Economics News</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.title("Daily Finance Brief")

if not dates:
    st.warning("Aucun brief disponible. Le premier sera généré à 08h30.")
    st.stop()

dcol1, dcol2 = st.columns([2, 1])
with dcol1:
    selected_date = st.selectbox(
        "Édition",
        options=dates,
        index=0,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
    )
with dcol2:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.caption(f"{len(dates)} éditions archivées")

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
        '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:12px">Marchés</div>',
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
            f'<div style="padding:4px 0 8px">'
            f'<div style="font-size:8px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#9CA3AF;margin-bottom:5px">{label}</div>'
            f'<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:20px;font-weight:700;color:#0B2545;letter-spacing:-0.5px;line-height:1">{data.get("value","—")}{unit}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{color};margin-top:4px">{arrow} {change or "—"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("---")

_gen = brief.get("generated_at", "")
st.caption(f"Généré le {_gen[:10]} à {_gen[11:16]} · {stats.get('collected', '?')} sources scannées")

if brief.get("low_volume"):
    st.warning("Volume réduit — seules les news les plus pertinentes ont été retenues.")

st.markdown("---")

# ── Filters ────────────────────────────────────────────────────────────────
cats_present    = sorted({item.get("category", "Sector") for item in news})
cat_options     = {CATEGORY_LABELS.get(c, c): c for c in cats_present}
sectors_present = sorted({item.get("sector", "Other") for item in news})

# Reset guard
if st.session_state.get("_reset_filters"):
    for k in ["main_region", "main_cat", "main_sector"]:
        st.session_state.pop(k, None)
    st.session_state.pop("_reset_filters", None)

with st.expander("Filtres", expanded=True):
    fcol1, fcol2, fcol3, fcol_reset = st.columns([1, 1, 1, 0.28])
    with fcol1:
        selected_regions = st.multiselect(
            "Région", _ALL_REGIONS, default=_ALL_REGIONS, key="main_region",
        )
    with fcol2:
        selected_labels = st.multiselect(
            "Type d'information", list(cat_options.keys()),
            default=list(cat_options.keys()), key="main_cat",
        )
        selected_cats = [cat_options[l] for l in selected_labels]
    with fcol3:
        selected_sectors = st.multiselect(
            "Secteur", sectors_present, default=sectors_present, key="main_sector",
        )
    with fcol_reset:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↺ Reset", use_container_width=True, help="Réinitialiser tous les filtres"):
            st.session_state["_reset_filters"] = True
            st.rerun()

# Apply filters
allowed_geos = _geos_for_regions(selected_regions) if selected_regions else set()
filtered_news = [
    n for n in news
    if n.get("category", "Sector") in selected_cats
    and n.get("sector", "Other") in selected_sectors
    and (not selected_regions or n.get("geography", "Global") in allowed_geos)
]

_filters_active = (
    len(selected_regions) < len(_ALL_REGIONS)
    or len(selected_cats) < len(cat_options)
    or len(selected_sectors) < len(sectors_present)
)
_filter_label = (
    f"{len(filtered_news)} news — filtrées" if _filters_active
    else f"{len(filtered_news)} news"
)
st.markdown(
    f'<div style="font-size:8px;font-weight:700;letter-spacing:3px;'
    f'text-transform:uppercase;color:#C9A84C;margin:10px 0 14px">{_filter_label}</div>',
    unsafe_allow_html=True,
)

# ── News cards ─────────────────────────────────────────────────────────────
for item in filtered_news:
    news_card(item)

# ── Exports ────────────────────────────────────────────────────────────────
st.markdown("---")
col_csv, col_info = st.columns([1, 3])

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
    st.caption(f"Brief du {selected_date} · {len(news)} news")
