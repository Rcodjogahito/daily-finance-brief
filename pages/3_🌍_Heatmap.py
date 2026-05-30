"""Page 3 — Heatmap deals secteur × géographie."""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.styles import inject_all, sidebar_nav, section_header

st.set_page_config(
    page_title="Heatmap — Daily Finance Brief",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_all()
sidebar_nav()

# ── Sidebar — paramètres page ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Paramètres")
    mode = st.radio("Mode", ["Volume (nb news)", "Valeur (Md€ deals)"], index=0)
    mode_key = "count" if "Volume" in mode else "value"
    period = st.selectbox(
        "Période",
        ["7 derniers jours", "30 derniers jours", "90 derniers jours", "YTD", "Tout"],
        index=2,
    )
    now = datetime.now()
    cutoff = {
        "7 derniers jours":  now - timedelta(days=7),
        "30 derniers jours": now - timedelta(days=30),
        "90 derniers jours": now - timedelta(days=90),
        "YTD":               datetime(now.year, 1, 1),
        "Tout":              datetime(2000, 1, 1),
    }[period]

# ── Header ─────────────────────────────────────────────────────────────────
section_header("Coffee Economics News")
st.title("Heatmap Deals")
st.markdown(
    '<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:20px">'
    'Flux de deals par secteur × géographie'
    '</div>',
    unsafe_allow_html=True,
)


# ── Load all news ──────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all_news() -> pd.DataFrame:
    rows = []
    for d in list_brief_dates():
        brief = load_brief(d)
        if not brief:
            continue
        for item in brief.get("news", []):
            rows.append({
                "date":         d,
                "sector":       item.get("sector", "Other"),
                "geography":    item.get("geography", "Global"),
                "category":     item.get("category", "Sector"),
                "deal_size_eur":item.get("deal_size_eur"),
                "url":          item.get("url", ""),
                "headline":     item.get("headline", item.get("title", "")),
                "source":       item.get("source", ""),
                "confidence":   item.get("confidence", "medium"),
            })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


with st.spinner("Chargement des données…"):
    df_all = load_all_news()

if df_all.empty:
    st.markdown(
        '<div style="background:#FFFFFF;border-radius:8px;padding:40px 32px;'
        'text-align:center;border:1px solid #E8EEF5;margin-top:24px">'
        '<div style="font-size:40px;margin-bottom:16px">🌍</div>'
        '<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:20px;'
        'font-weight:700;color:#071828;margin-bottom:10px">Aucune donnée disponible</div>'
        '<div style="font-size:14px;color:#6B7A8E">'
        'Les heatmaps seront disponibles après la première exécution du pipeline.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Category filter in sidebar
with st.sidebar:
    all_cats = df_all["category"].unique().tolist()
    selected_cat = st.selectbox("Catégorie", ["Toutes"] + sorted(all_cats))

# ── Filter ─────────────────────────────────────────────────────────────────
df = df_all[df_all["date"] >= pd.Timestamp(cutoff)].copy()
if selected_cat != "Toutes":
    df = df[df["category"] == selected_cat]

if df.empty:
    st.warning("Aucune donnée pour les filtres sélectionnés.")
    st.stop()

# ── Heatmap ────────────────────────────────────────────────────────────────
SECTOR_ORDER = [
    "Energy", "Commodities", "Financials", "TMT", "Healthcare", "Industrials",
    "Aviation", "Defense", "Consumer", "Luxury", "Entertainment",
    "Real Estate", "Materials", "Services", "Other",
]
GEO_ORDER = [
    "France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux",
    "Other Europe", "USA", "Canada", "MENA", "Africa", "Asia", "LatAm", "Global",
]

if mode_key == "count":
    pivot = df.pivot_table(
        index="sector", columns="geography",
        values="url", aggfunc="count", fill_value=0,
    )
    color_label = "Nb news"
    title_hm = "Volume — Nb news par secteur × géographie"
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
    title_hm = "Valeur — Montant deals (Md€) par secteur × géographie"

sectors_present = [s for s in SECTOR_ORDER if s in pivot.index] + [s for s in pivot.index if s not in SECTOR_ORDER]
geos_present    = [g for g in GEO_ORDER if g in pivot.columns] + [g for g in pivot.columns if g not in GEO_ORDER]
pivot = pivot.reindex(index=sectors_present, columns=geos_present, fill_value=0)

st.markdown("---")
section_header(title_hm)

fig = px.imshow(
    pivot,
    color_continuous_scale=[[0, "#EFF6FF"], [0.4, "#3B82F6"], [1, "#0B2545"]],
    aspect="auto",
    text_auto=True,
    labels={"color": color_label},
)
fig.update_layout(
    height=520,
    margin=dict(t=20, b=10, l=10, r=10),
    coloraxis_colorbar=dict(
        title=color_label,
        title_font_size=11,
        tickfont_size=10,
    ),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font_family="Inter, Helvetica Neue, Arial, sans-serif",
    font_color="#374151",
    font_size=11,
)
fig.update_xaxes(tickangle=-35, tickfont=dict(size=10))
fig.update_yaxes(tickfont=dict(size=10))
st.plotly_chart(fig, use_container_width=True)

# ── Detail table ───────────────────────────────────────────────────────────
st.markdown("---")
section_header("Détail par filtre")
col1, col2 = st.columns(2)
with col1:
    sector_filter = st.selectbox("Secteur", ["Tous"] + sectors_present)
with col2:
    geo_filter = st.selectbox("Géographie", ["Toutes"] + geos_present)

df_detail = df.copy()
if sector_filter != "Tous":
    df_detail = df_detail[df_detail["sector"] == sector_filter]
if geo_filter != "Toutes":
    df_detail = df_detail[df_detail["geography"] == geo_filter]

st.caption(f"{len(df_detail)} news correspondantes")

if not df_detail.empty:
    for _, row in df_detail.head(30).iterrows():
        url = row.get("url", "")
        headline = (row.get("headline", "") or "")[:90]
        deal_str = (
            f'<span style="display:inline-block;background:#EBF4FF;color:#0B2545;'
            f'padding:2px 7px;border-radius:2px;font-size:9px;font-weight:700;margin-left:6px">'
            f'{row["deal_size_eur"]/1e9:.1f} Md€</span>'
            if pd.notna(row.get("deal_size_eur")) else ""
        )
        href = f'href="{url}" target="_blank"' if url else ""
        st.markdown(
            f'<div style="padding:10px 14px;background:#FFFFFF;border:1px solid #E8EEF5;'
            f'border-radius:4px;margin-bottom:6px">'
            f'<div style="margin-bottom:5px">'
            f'<a {href} style="font-size:13.5px;font-weight:600;color:#071828;'
            f'text-decoration:none">{headline}</a>{deal_str}'
            f'</div>'
            f'<div style="font-size:10.5px;color:#9CA3AF">'
            f'{row["source"]} · {row["geography"]} · {str(row["date"])[:10]}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Top 10 deals ───────────────────────────────────────────────────────────
st.markdown("---")
section_header("Top 10 deals par montant")

df_top = df[df["deal_size_eur"].notna()].copy()
df_top = df_top.sort_values("deal_size_eur", ascending=False).head(10)

if df_top.empty:
    st.info("Aucun montant de deal identifié dans cette période.")
else:
    df_top["Montant (Md€)"] = (df_top["deal_size_eur"] / 1e9).round(1)
    df_top["Date"] = df_top["date"].dt.strftime("%Y-%m-%d")
    df_top["Titre"] = df_top["headline"].str[:55]

    fig2 = px.bar(
        df_top, x="Montant (Md€)", y="Titre",
        orientation="h",
        color="sector",
        height=420,
        text="Montant (Md€)",
    )
    fig2.update_layout(
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        xaxis=dict(tickfont=dict(size=10)),
        margin=dict(t=20, b=20, l=0, r=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_family="Inter, Helvetica Neue, Arial, sans-serif",
        font_color="#374151",
        legend_title_text="Secteur",
        legend=dict(font=dict(size=10)),
    )
    fig2.update_traces(texttemplate="%{text:.1f} Md€", textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)
