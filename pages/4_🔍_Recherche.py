"""Page 4 — Recherche full-text."""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.archiver import list_brief_dates, load_brief

st.set_page_config(page_title="Recherche — Daily Finance Brief", page_icon="🔍", layout="wide")

st.title("🔍 Recherche full-text")


@st.cache_data(ttl=3600)
def load_all_news_flat() -> list[dict]:
    dates = list_brief_dates()
    rows = []
    for d in dates:
        brief = load_brief(d)
        if not brief:
            continue
        for item in brief.get("news", []):
            rows.append({
                "date": d,
                "rank": item.get("rank", 0),
                "category": item.get("category", "Sector"),
                "headline": item.get("headline", item.get("title", "")),
                "source": item.get("source", ""),
                "sector": item.get("sector", "Other"),
                "geography": item.get("geography", "Global"),
                "confidence": item.get("confidence", "medium"),
                "deal_size_eur": item.get("deal_size_eur"),
                "url": item.get("url", ""),
                "summary": item.get("summary", ""),
                "so_what": item.get("so_what", ""),
                "source_count": item.get("source_count", 1),
            })
    return rows


all_news = load_all_news_flat()

if not all_news:
    st.warning("Aucune donnée disponible.")
    st.stop()

# ── Search box ────────────────────────────────────────────────────────────
query = st.text_input("Rechercher dans les headlines, résumés et So what", placeholder="ex: LBO, TotalEnergies, refinancing, ECB...")

# ── Advanced filters ──────────────────────────────────────────────────────
with st.expander("Filtres avancés", expanded=bool(query)):
    col1, col2 = st.columns(2)
    with col1:
        date_min = st.date_input("Date min", value=datetime.now() - timedelta(days=90))
        cats = sorted({n["category"] for n in all_news})
        selected_cats = st.multiselect("Catégories", cats, default=cats)
        sectors = sorted({n["sector"] for n in all_news})
        selected_sectors = st.multiselect("Secteurs", sectors, default=sectors)
    with col2:
        date_max = st.date_input("Date max", value=datetime.now())
        sources = sorted({n["source"] for n in all_news})
        selected_sources = st.multiselect("Sources", sources, default=sources)
        geos = sorted({n["geography"] for n in all_news})
        selected_geos = st.multiselect("Géographies", geos, default=geos)
    confidence_filter = st.radio("Confidence", ["Toutes", "High only"], horizontal=True)

# ── Filter logic ──────────────────────────────────────────────────────────
def matches_query(item: dict, q: str) -> bool:
    if not q:
        return True
    q_lower = q.lower()
    return any(
        q_lower in (item.get(field, "") or "").lower()
        for field in ("headline", "summary", "so_what", "source")
    )


def highlight(text: str, query: str) -> str:
    if not query or not text:
        return text
    import re
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return pattern.sub(
        lambda m: f'<mark style="background:#FEF08A;padding:0 2px">{m.group()}</mark>',
        text,
    )


results = [
    n for n in all_news
    if matches_query(n, query)
    and n.get("date", "") >= str(date_min)
    and n.get("date", "") <= str(date_max)
    and n.get("category", "") in selected_cats
    and n.get("sector", "") in selected_sectors
    and n.get("source", "") in selected_sources
    and n.get("geography", "") in selected_geos
    and (confidence_filter == "Toutes" or n.get("confidence") == "high")
]

results.sort(key=lambda n: n.get("date", ""), reverse=True)

# ── Results ───────────────────────────────────────────────────────────────
st.markdown(f"**{len(results)} résultats**")

if not results:
    st.info("Aucun résultat. Essayez d'élargir les filtres ou de modifier la recherche.")
    st.stop()

# Export buttons
col_csv1, col_csv2 = st.columns(2)
with col_csv1:
    df_export = pd.DataFrame([{k: v for k, v in r.items() if k != "so_what"} for r in results])
    csv_data = df_export.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Exporter CSV complet", data=csv_data, file_name="recherche_brief.csv", mime="text/csv")
with col_csv2:
    import io as _io, csv as _csv
    buf = _io.StringIO()
    w = _csv.writer(buf, quoting=_csv.QUOTE_ALL)
    w.writerow(["Date", "Category", "Headline", "Source", "Sector", "Geography",
                "Deal_Size_Bn_EUR", "Confidence", "URL"])
    for r in results:
        deal = r.get("deal_size_eur")
        w.writerow([
            r.get("date", ""), r.get("category", ""), r.get("headline", ""),
            r.get("source", ""), r.get("sector", ""), r.get("geography", ""),
            f"{deal/1e9:.2f}" if deal else "",
            r.get("confidence", ""), r.get("url", ""),
        ])
    bloomberg_csv = buf.getvalue().encode("utf-8-sig")
    st.download_button(
        "📊 Export Bloomberg CSV",
        data=bloomberg_csv,
        file_name="bloomberg_deal_flow.csv",
        mime="text/csv",
        help="Format compatible Bloomberg Terminal / Excel deal tracker",
    )

st.markdown("---")

CATEGORY_COLORS = {
    "M&A": "#16A34A", "LevFin": "#EA580C", "Energy": "#7C3AED",
    "Credit": "#2563EB", "Macro": "#475569", "Geo": "#DC2626",
    "Reg": "#CA8A04", "Sector": "#0891B2",
}

for item in results:
    cat = item.get("category", "Sector")
    color = CATEGORY_COLORS.get(cat, "#64748b")
    deal = f" — **{item['deal_size_eur']/1e9:.1f} Md€**" if item.get("deal_size_eur") else ""
    multi = f" ✓ {item['source_count']} sources" if item.get("source_count", 1) >= 2 else ""

    hl_headline = highlight(item.get("headline", ""), query)
    hl_summary = highlight(item.get("summary", ""), query)
    hl_so_what = highlight(item.get("so_what", ""), query)

    with st.container():
        st.markdown(
            f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700">{cat}</span>'
            f'&nbsp;<span style="font-size:12px;color:#64748b">{item.get("date","")} &nbsp; {item.get("source","")}</span>'
            f'{deal}<span style="color:#16A34A;font-size:12px">{multi}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<h4><a href="{item.get("url","")}" target="_blank" style="color:#0A1F44;text-decoration:none">{hl_headline}</a></h4>',
            unsafe_allow_html=True,
        )
        st.caption(f"📍 {item.get('geography','')} &nbsp; 🏭 {item.get('sector','')}")
        st.markdown(f"<div style='font-size:13.5px'>{hl_summary}</div>", unsafe_allow_html=True)
        if hl_so_what:
            st.markdown(
                f'<div style="background:#F0F9FF;border-left:3px solid #0891B2;padding:8px 12px;font-size:13px;border-radius:0 4px 4px 0;margin-top:6px">'
                f'<strong style="font-size:11px;color:#0891B2">💡 SO WHAT</strong><br>{hl_so_what}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("---")
