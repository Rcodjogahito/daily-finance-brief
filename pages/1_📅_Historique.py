"""Page 1 — Historique."""
from datetime import datetime

import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.enrichment import REGION_GEO_MAP
from src.styles import inject_css, sidebar_brand, page_toolbar, news_card, CATEGORY_LABELS

st.set_page_config(page_title="Historique — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()

page_toolbar()

st.markdown(
    '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:5px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Historique des briefs")

_ALL_REGIONS = ["Europe", "EMEA", "APAC", "Afrique", "Amériques", "Global"]

dates = list_brief_dates()
if not dates:
    st.warning("Aucun brief archivé.")
    st.stop()

with st.sidebar:
    st.markdown("### Édition")
    selected_date = st.selectbox(
        "Date",
        options=dates,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
        label_visibility="collapsed",
    )
    st.caption(f"{len(dates)} éditions archivées")
    st.markdown("---")
    st.markdown("### Filtres")

    all_cats = [
        "M&A", "LevFin", "Energy", "Credit", "Macro", "Geo", "Reg", "Sector", "Nominations", "Banking",
    ]
    cat_label_map = {CATEGORY_LABELS.get(c, c): c for c in all_cats}
    selected_cat_labels = st.multiselect(
        "Type d'information", list(cat_label_map.keys()), default=list(cat_label_map.keys()),
    )
    selected_cats = [cat_label_map[l] for l in selected_cat_labels]

    all_regions = _ALL_REGIONS
    selected_regions = st.multiselect("Région", all_regions, default=all_regions)

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

brief = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news = brief.get("news", [])

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

date_fmt = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize()
s = brief.get("stats", {})
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sources scannées", s.get("collected", "—"))
c2.metric("News sélectionnées", len(news))
c3.metric("Affichées", len(filtered))
c4.metric("Date", date_fmt.split(" ")[0].capitalize() + " " + date_fmt.split(" ")[1])

if not filtered:
    st.info("Aucune news ne correspond aux filtres sélectionnés.")
    st.stop()

st.markdown("---")

for item in filtered:
    news_card(item)

