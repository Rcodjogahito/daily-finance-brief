"""Page 4 — Recherche full-text."""
import io as _io
import csv as _csv
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.enrichment import REGION_GEO_MAP
from src.styles import inject_css, sidebar_brand, page_toolbar, news_card, CATEGORY_LABELS

st.set_page_config(page_title="Recherche — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()

page_toolbar()

st.markdown(
    '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:5px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Recherche")

_ALL_REGIONS = ["Europe", "EMEA", "APAC", "Afrique", "Amériques", "Global"]


@st.cache_data(ttl=3600)
def load_all_news_flat() -> list[dict]:
    rows = []
    for d in list_brief_dates():
        brief = load_brief(d)
        if not brief:
            continue
        for item in brief.get("news", []):
            rows.append({
                "date":         d,
                "rank":         item.get("rank", 0),
                "category":     item.get("category", "Sector"),
                "headline":     item.get("headline", item.get("title", "")),
                "source":       item.get("source", ""),
                "sector":       item.get("sector", "Other"),
                "geography":    item.get("geography", "Global"),
                "region":       item.get("region", "Global"),
                "confidence":   item.get("confidence", "medium"),
                "deal_size_eur":item.get("deal_size_eur"),
                "url":          item.get("url", ""),
                "summary":      item.get("summary", ""),
                "so_what":      item.get("so_what", ""),
                "source_count": item.get("source_count", 1),
            })
    return rows


all_news = load_all_news_flat()

if not all_news:
    st.warning("Aucune donnée disponible.")
    st.stop()

# ── Sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres")

    date_min = st.date_input("Date min", value=datetime.now() - timedelta(days=90))
    date_max = st.date_input("Date max", value=datetime.now())

    st.markdown("---")

    all_cat_keys = sorted({n["category"] for n in all_news})
    cat_label_map = {CATEGORY_LABELS.get(c, c): c for c in all_cat_keys}
    selected_cat_labels = st.multiselect(
        "Type d'information", list(cat_label_map.keys()), default=list(cat_label_map.keys())
    )
    selected_cats = [cat_label_map[l] for l in selected_cat_labels]

    selected_regions = st.multiselect("Région", _ALL_REGIONS, default=_ALL_REGIONS)

    sources = sorted({n["source"] for n in all_news})
    selected_sources = st.multiselect("Sources", sources, default=sources)

    sectors = sorted({n["sector"] for n in all_news})
    selected_sectors = st.multiselect("Secteurs", sectors, default=sectors)

    confidence_filter = st.radio("Fiabilité", ["Toutes", "High only"], horizontal=True)

# ── Search bar ─────────────────────────────────────────────────────────────
query = st.text_input(
    "Recherche",
    placeholder="ex: LBO, TotalEnergies, BCE, refinancement, nominated...",
)

# Build allowed geos from region filter
allowed_geos: set[str] = set()
for r in selected_regions:
    allowed_geos |= REGION_GEO_MAP.get(r, set())


def matches(item: dict, q: str) -> bool:
    if not q:
        return True
    q = q.lower()
    return any(
        q in (item.get(f, "") or "").lower()
        for f in ("headline", "summary", "so_what", "source")
    )


def highlight(text: str, q: str) -> str:
    if not q or not text:
        return text
    import re
    return re.compile(re.escape(q), re.IGNORECASE).sub(
        lambda m: f'<mark style="background:#FEF3C7;padding:0 2px;border-radius:1px">{m.group()}</mark>',
        text,
    )


results = [
    n for n in all_news
    if matches(n, query)
    and str(date_min) <= n.get("date", "") <= str(date_max)
    and n.get("category", "") in selected_cats
    and n.get("sector", "") in selected_sectors
    and n.get("source", "") in selected_sources
    and (not selected_regions or n.get("geography", "Global") in allowed_geos)
    and (confidence_filter == "Toutes" or n.get("confidence") == "high")
]
results.sort(key=lambda n: n.get("date", ""), reverse=True)

st.markdown("---")
st.markdown(
    f'<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:12px">{len(results)} résultats</div>',
    unsafe_allow_html=True,
)

if not results:
    st.info("Aucun résultat. Élargissez les filtres ou modifiez la recherche.")
    st.stop()

# ── Export ─────────────────────────────────────────────────────────────────
col_e1, col_e2, _ = st.columns([1, 1, 3])
with col_e1:
    df_export = pd.DataFrame([{k: v for k, v in r.items() if k != "so_what"} for r in results])
    st.download_button(
        "Export CSV",
        data=df_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="recherche_brief.csv",
        mime="text/csv",
    )
with col_e2:
    buf = _io.StringIO()
    w   = _csv.writer(buf, quoting=_csv.QUOTE_ALL)
    w.writerow(["Date", "Category", "Headline", "Source", "Sector", "Geography", "Region", "Deal_Size_Bn_EUR", "Confidence", "URL"])
    for r in results:
        deal = r.get("deal_size_eur")
        w.writerow([
            r.get("date",""), r.get("category",""), r.get("headline",""),
            r.get("source",""), r.get("sector",""), r.get("geography",""),
            r.get("region",""),
            f"{deal/1e9:.2f}" if deal else "", r.get("confidence",""), r.get("url",""),
        ])
    st.download_button(
        "Export Bloomberg CSV",
        data=buf.getvalue().encode("utf-8-sig"),
        file_name="bloomberg_recherche.csv",
        mime="text/csv",
        help="Format compatible Bloomberg Terminal / Excel deal tracker",
    )

st.markdown("---")

# ── Results ────────────────────────────────────────────────────────────────
hl = lambda t: highlight(t, query)

for item in results:
    news_card(item, highlight_fn=hl)
