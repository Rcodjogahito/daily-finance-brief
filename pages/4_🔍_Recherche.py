"""Page 4 — Recherche full-text."""
import io as _io
import csv as _csv
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.enrichment import REGION_GEO_MAP
from src.styles import inject_css, sidebar_brand, news_card, section_header, CATEGORY_LABELS

st.set_page_config(
    page_title="Recherche — Daily Finance Brief",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

_ALL_REGIONS = ["Europe", "EMEA", "APAC", "Afrique", "Amériques", "Global"]

# ── Sidebar nav ────────────────────────────────────────────────────────────
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

    st.markdown("### Filtres")
    date_min = st.date_input("Date min", value=datetime.now() - timedelta(days=90))
    date_max = st.date_input("Date max", value=datetime.now())
    st.markdown("---")


# ── Header ─────────────────────────────────────────────────────────────────
section_header("Coffee Economics News")
st.title("Recherche")
st.markdown(
    '<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:20px">'
    'Recherche full-text sur l\'ensemble des briefs archivés'
    '</div>',
    unsafe_allow_html=True,
)


# ── Load data ──────────────────────────────────────────────────────────────
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


with st.spinner("Indexation des briefs…"):
    all_news = load_all_news_flat()

if not all_news:
    st.markdown(
        '<div style="background:#FFFFFF;border-radius:8px;padding:40px 32px;'
        'text-align:center;border:1px solid #E8EEF5;margin-top:24px">'
        '<div style="font-size:40px;margin-bottom:16px">🔍</div>'
        '<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:20px;'
        'font-weight:700;color:#071828;margin-bottom:10px">Index vide</div>'
        '<div style="font-size:14px;color:#6B7A8E">'
        'Aucun brief archivé pour le moment. La recherche sera disponible après la première génération.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    all_cat_keys = sorted({n["category"] for n in all_news})
    cat_label_map = {CATEGORY_LABELS.get(c, c): c for c in all_cat_keys}
    selected_cat_labels = st.multiselect(
        "Type", list(cat_label_map.keys()), default=list(cat_label_map.keys()),
    )
    selected_cats = [cat_label_map[l] for l in selected_cat_labels]

    selected_regions = st.multiselect("Région", _ALL_REGIONS, default=_ALL_REGIONS)

    sources = sorted({n["source"] for n in all_news})
    selected_sources = st.multiselect("Sources", sources, default=sources)

    sectors = sorted({n["sector"] for n in all_news})
    selected_sectors = st.multiselect("Secteurs", sectors, default=sectors)

    confidence_filter = st.radio("Fiabilité", ["Toutes", "High only"], horizontal=True)
    st.markdown("---")
    if st.button("↺ Réinitialiser", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("4_") or k == "query":
                st.session_state.pop(k, None)
        st.rerun()

# ── Search bar ─────────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:#FFFFFF;border-radius:8px;padding:20px 20px 16px;'
    'border:1px solid #E8EEF5;box-shadow:0 1px 4px rgba(11,37,69,0.04);margin-bottom:16px">',
    unsafe_allow_html=True,
)
scol1, scol2 = st.columns([4, 1])
with scol1:
    query = st.text_input(
        "Recherche",
        placeholder="ex: LBO, TotalEnergies, BCE, refinancement, M&A…",
        label_visibility="collapsed",
        key="query",
    )
with scol2:
    st.caption(f"{len(all_news)} news\nindexées")
st.markdown('</div>', unsafe_allow_html=True)

# Build allowed geos
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
        lambda m: (
            f'<mark style="background:#FEF3C7;color:#92400E;padding:0 2px;'
            f'border-radius:2px;font-weight:600">{m.group()}</mark>'
        ),
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

# ── Results header ─────────────────────────────────────────────────────────
st.markdown("---")
res_label = f"{len(results)} résultat{'s' if len(results) != 1 else ''}"
if query:
    res_label += f" pour « {query} »"
section_header(res_label)

if not results:
    st.info("Aucun résultat. Essayez des mots-clés différents ou élargissez les filtres.")
    st.stop()

# ── Export ─────────────────────────────────────────────────────────────────
col_e1, col_e2, _ = st.columns([1, 1, 3])
with col_e1:
    df_export = pd.DataFrame([{k: v for k, v in r.items() if k != "so_what"} for r in results])
    st.download_button(
        "⬇ Export CSV",
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
            r.get("region",""), f"{deal/1e9:.2f}" if deal else "",
            r.get("confidence",""), r.get("url",""),
        ])
    st.download_button(
        "⬇ Bloomberg CSV",
        data=buf.getvalue().encode("utf-8-sig"),
        file_name="bloomberg_recherche.csv",
        mime="text/csv",
        help="Format compatible Bloomberg Terminal",
    )

st.markdown("---")

# ── Results ────────────────────────────────────────────────────────────────
hl = lambda t: highlight(t, query) if query else t

for item in results:
    news_card(item, highlight_fn=(hl if query else None))
