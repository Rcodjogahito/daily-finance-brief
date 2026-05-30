"""Page 1 — Historique des briefs."""
from datetime import datetime

import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.enrichment import REGION_GEO_MAP
from src.styles import inject_all, sidebar_brand, news_card, section_header, CATEGORY_LABELS

st.set_page_config(
    page_title="Historique — Daily Finance Brief",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_all()
sidebar_brand()

_ALL_REGIONS = ["Europe", "EMEA", "Afrique", "APAC", "Amériques", "Global"]

# ── Sidebar ────────────────────────────────────────────────────────────────
dates = list_brief_dates()

with st.sidebar:
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("streamlit_app.py",              label="📰  Brief du jour")
    st.page_link("pages/1_📅_Historique.py",      label="📅  Historique")
    st.page_link("pages/2_🔥_Alertes.py",         label="🔥  Alertes intraday")
    st.page_link("pages/3_🌍_Heatmap.py",         label="🌍  Heatmap deals")
    st.page_link("pages/4_🔍_Recherche.py",        label="🔍  Recherche")
    st.page_link("pages/5_📧_Abonnement.py",       label="📧  Abonnement")
    st.markdown("---")

if not dates:
    st.warning("Aucun brief archivé.")
    st.stop()

with st.sidebar:
    st.markdown("### Édition")
    selected_date = st.selectbox(
        "Date",
        options=dates,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y"),
        label_visibility="collapsed",
    )
    st.caption(f"{len(dates)} éditions archivées")
    st.markdown("---")

    st.markdown("### Filtres")
    all_cats = list(CATEGORY_LABELS.keys())
    cat_label_map = {CATEGORY_LABELS.get(c, c): c for c in all_cats}
    selected_cat_labels = st.multiselect(
        "Type d'information", list(cat_label_map.keys()), default=list(cat_label_map.keys()),
    )
    selected_cats = [cat_label_map[l] for l in selected_cat_labels]

    selected_regions = st.multiselect("Région", _ALL_REGIONS, default=_ALL_REGIONS)

    all_sectors = [
        "Energy", "Financials", "Healthcare", "TMT", "Industrials",
        "Aviation", "Defense", "Consumer", "Luxury", "Entertainment",
        "Real Estate", "Materials", "Services", "Other",
    ]
    selected_sectors = st.multiselect("Secteurs", all_sectors, default=all_sectors)
    if st.button("↺ Réinitialiser", use_container_width=True):
        for k in ["1_region", "1_cat", "1_sector"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────
section_header("Coffee Economics News")
st.title("Historique des briefs")

date_fmt = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize()
st.markdown(
    f'<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:20px">'
    f'{date_fmt}'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Load brief ─────────────────────────────────────────────────────────────
brief = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news = brief.get("news", [])
s    = brief.get("stats", {})

# Resolve region filter to geographies
allowed_geos: set[str] = set()
for r in selected_regions:
    allowed_geos |= REGION_GEO_MAP.get(r, set())

filtered = [
    n for n in news
    if n.get("category", "Sector") in selected_cats
    and n.get("sector", "Other") in selected_sectors
    and (not selected_regions or n.get("geography", "Global") in allowed_geos)
]

# ── Stats ──────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sources scannées", s.get("collected", "—"))
c2.metric("News sélectionnées", len(news))
c3.metric("Affichées", len(filtered))
c4.metric(
    "Email envoyé",
    "✓ Oui" if s.get("email_sent") else "Non",
)
st.markdown("---")

# ── News ───────────────────────────────────────────────────────────────────
section_header(f"{len(filtered)} news affichées")

if not filtered:
    st.info("Aucune news ne correspond aux filtres sélectionnés.")
    st.stop()

for item in filtered:
    news_card(item)
