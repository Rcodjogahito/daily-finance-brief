"""Page 3 — Heatmap deals secteur × géographie."""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.styles import inject_css, sidebar_brand, page_toolbar

st.set_page_config(page_title="Heatmap — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()
page_toolbar()

st.markdown(
    '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Heatmap Deals Secteur x Géographie")

# Load all news from all briefs
@st.cache_data(ttl=3600)
def load_all_news() -> pd.DataFrame:
    dates = list_brief_dates()
    rows = []
    for d in dates:
        brief = load_brief(d)
        if not brief:
            continue
        for item in brief.get("news", []):
            rows.append({
                "date": d,
                "sector": item.get("sector", "Other"),
                "geography": item.get("geography", "Global"),
                "category": item.get("category", "Sector"),
                "deal_size_eur": item.get("deal_size_eur"),
                "url": item.get("url", ""),
                "headline": item.get("headline", item.get("title", "")),
                "source": item.get("source", ""),
                "confidence": item.get("confidence", "medium"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df

df_all = load_all_news()

if df_all.empty:
    st.warning("Aucune donnée disponible. Les briefs seront disponibles après la première exécution automatique.")
    st.stop()

# ── Sidebar filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Paramètres Heatmap")

    mode = st.radio("Mode", ["Volume (nb news)", "Valeur (Md€ deals)"], index=0)
    mode_key = "count" if "Volume" in mode else "value"

    period = st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "90 derniers jours", "YTD", "Tout"])
    now = datetime.now()
    if period == "7 derniers jours":
        cutoff = now - timedelta(days=7)
    elif period == "30 derniers jours":
        cutoff = now - timedelta(days=30)
    elif period == "90 derniers jours":
        cutoff = now - timedelta(days=90)
    elif period == "YTD":
        cutoff = datetime(now.year, 1, 1)
    else:
        cutoff = datetime(2000, 1, 1)

    all_cats = df_all["category"].unique().tolist()
    selected_cat = st.selectbox("Catégorie", ["Toutes"] + sorted(all_cats))

# Filter by period + category
df = df_all[df_all["date"] >= pd.Timestamp(cutoff)].copy()
if selected_cat != "Toutes":
    df = df[df["category"] == selected_cat]

if df.empty:
    st.warning("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

# ── Heatmap ────────────────────────────────────────────────────────────────
SECTOR_ORDER = ["Energy", "Financials", "TMT", "Healthcare", "Industrials",
                "Aviation", "Defense", "Consumer", "Luxury", "Entertainment",
                "Real Estate", "Materials", "Services", "Other"]
GEO_ORDER = ["France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux",
             "Other Europe", "USA", "Canada", "MENA", "Africa", "Asia", "LatAm", "Global"]

if mode_key == "count":
    pivot = df.pivot_table(
        index="sector", columns="geography",
        values="url", aggfunc="count", fill_value=0,
    )
    color_label = "Nb news"
    title = "Heatmap Volume — Nb news par secteur × géographie"
else:
    df_deals = df[df["deal_size_eur"].notna()].copy()
    df_deals["deal_size_eur_bn"] = df_deals["deal_size_eur"] / 1e9
    if df_deals.empty:
        st.warning("Aucun deal avec montant identifié dans cette période.")
        st.stop()
    pivot = df_deals.pivot_table(
        index="sector", columns="geography",
        values="deal_size_eur_bn", aggfunc="sum", fill_value=0,
    )
    color_label = "Md€"
    title = "Heatmap Valeur — Montant deals (Md€) par secteur × géographie"

# Reorder axes
sectors_present = [s for s in SECTOR_ORDER if s in pivot.index] + [s for s in pivot.index if s not in SECTOR_ORDER]
geos_present = [g for g in GEO_ORDER if g in pivot.columns] + [g for g in pivot.columns if g not in GEO_ORDER]
pivot = pivot.reindex(index=sectors_present, columns=geos_present, fill_value=0)

fig = px.imshow(
    pivot,
    color_continuous_scale="Blues",
    aspect="auto",
    text_auto=True,
    title=title,
    labels={"color": color_label},
)
fig.update_layout(
    height=500,
    margin=dict(t=60, b=20, l=20, r=20),
    coloraxis_colorbar=dict(title=color_label),
)
fig.update_xaxes(tickangle=-30)

st.plotly_chart(fig, use_container_width=True)

# ── Click-to-filter detail table ───────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    sector_filter = st.selectbox("Détail secteur", ["Tous"] + sectors_present)
with col2:
    geo_filter = st.selectbox("Détail géographie", ["Toutes"] + geos_present)

df_detail = df.copy()
if sector_filter != "Tous":
    df_detail = df_detail[df_detail["sector"] == sector_filter]
if geo_filter != "Toutes":
    df_detail = df_detail[df_detail["geography"] == geo_filter]

st.markdown(f"**{len(df_detail)} news correspondantes**")

if not df_detail.empty:
    for _, row in df_detail.iterrows():
        deal_str = f" — **{row['deal_size_eur']/1e9:.1f} Md€**" if pd.notna(row.get("deal_size_eur")) else ""
        st.markdown(
            f"- [{row['headline'][:80]}]({row['url']}){deal_str}  \n"
            f"  {row['source']} · {row['geography']} · {str(row['date'])[:10]}"
        )

# ── Top 10 deals ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:12px">Top 10 deals par montant</div>',
    unsafe_allow_html=True,
)

df_top = df[df["deal_size_eur"].notna()].copy()
df_top = df_top.sort_values("deal_size_eur", ascending=False).head(10)

if df_top.empty:
    st.info("Aucun montant de deal identifié dans cette période.")
else:
    df_top["Montant (Md€)"] = (df_top["deal_size_eur"] / 1e9).round(1)
    df_top["Date"] = df_top["date"].dt.strftime("%Y-%m-%d")

    fig2 = px.bar(
        df_top, x="Montant (Md€)", y="headline",
        orientation="h",
        color="sector",
        title="Top 10 deals par taille",
        height=400,
        text="Montant (Md€)",
    )
    fig2.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)
