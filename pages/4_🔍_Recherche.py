"""Page 4 — Recherche full-text."""
import io as _io
import csv as _csv
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.styles import inject_css, sidebar_brand, news_card

st.set_page_config(page_title="Recherche — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()

st.markdown(
    '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Recherche")


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

# ── Search ─────────────────────────────────────────────────────────────────
query = st.text_input(
    "Recherche",
    placeholder="ex: LBO, TotalEnergies, BCE, refinancement...",
)

with st.expander("Filtres avancés", expanded=bool(query)):
    col1, col2 = st.columns(2)
    with col1:
        date_min       = st.date_input("Date min", value=datetime.now() - timedelta(days=90))
        cats           = sorted({n["category"] for n in all_news})
        selected_cats  = st.multiselect("Catégories", cats, default=cats)
        sectors        = sorted({n["sector"] for n in all_news})
        selected_sectors = st.multiselect("Secteurs", sectors, default=sectors)
    with col2:
        date_max       = st.date_input("Date max", value=datetime.now())
        sources        = sorted({n["source"] for n in all_news})
        selected_sources = st.multiselect("Sources", sources, default=sources)
        geos           = sorted({n["geography"] for n in all_news})
        selected_geos  = st.multiselect("Géographies", geos, default=geos)
    confidence_filter = st.radio("Fiabilité", ["Toutes", "High only"], horizontal=True)


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
    and n.get("geography", "") in selected_geos
    and (confidence_filter == "Toutes" or n.get("confidence") == "high")
]
results.sort(key=lambda n: n.get("date", ""), reverse=True)

st.markdown("---")
st.markdown(
    f'<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:12px">{len(results)} résultats</div>',
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
    w.writerow(["Date", "Category", "Headline", "Source", "Sector", "Geography", "Deal_Size_Bn_EUR", "Confidence", "URL"])
    for r in results:
        deal = r.get("deal_size_eur")
        w.writerow([
            r.get("date",""), r.get("category",""), r.get("headline",""),
            r.get("source",""), r.get("sector",""), r.get("geography",""),
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
