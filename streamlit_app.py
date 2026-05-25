"""Daily Finance Brief — Page principale (Brief du jour)."""
import io as _io
import csv as _csv
from datetime import datetime

import pytz
import streamlit as st

# ── Auto-refresh toutes les 30 min pour maintenir la connexion Streamlit active
# Empêche Streamlit Cloud de détecter l'inactivité WebSocket et d'endormir l'app.
try:
    from streamlit_autorefresh import st_autorefresh
    _count = st_autorefresh(interval=10 * 60 * 1000, key="keepalive_refresh")  # 10 min
except ImportError:
    pass  # Module optionnel — le keep-alive GitHub Actions prend le relais

from src.archiver import list_brief_dates, list_alert_dates, load_brief, load_alerts
from src.enrichment import REGION_GEO_MAP
from src.styles import (
    inject_css, sidebar_brand, news_card, section_header, status_badge,
    CATEGORY_COLORS, CATEGORY_LABELS, ALL_CATEGORIES,
)

_ALL_REGIONS = ["Europe", "EMEA", "APAC", "Afrique", "Amériques", "Global"]
_PARIS = pytz.timezone("Europe/Paris")


def _geos_for_regions(selected_regions: list[str]) -> set[str]:
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


# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Daily Finance Brief — Coffee Economics News",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Auth (optionnel) ───────────────────────────────────────────────────────
_pwd = st.secrets.get("DASHBOARD_PASSWORD", "") if hasattr(st, "secrets") else ""
if _pwd:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;
                    background:#F4F6FA">
        </div>
        """, unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1.2, 1])
        with col:
            st.markdown(
                '<div style="text-align:center;margin-bottom:24px">'
                '<div style="font-size:8px;font-weight:700;letter-spacing:3px;'
                'text-transform:uppercase;color:#C9A84C;margin-bottom:10px">'
                'Coffee Economics News</div>'
                '<div style="font-family:\'Playfair Display\',Georgia,serif;'
                'font-size:26px;font-weight:800;color:#071828">Daily Finance Brief</div>'
                '<div style="font-size:13px;color:#6B7A8E;margin-top:8px">'
                'Plateforme de veille CIB</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            with st.container():
                pwd = st.text_input("Mot de passe", type="password", placeholder="••••••••")
                if st.button("Accéder à la plateforme", use_container_width=True):
                    if pwd == _pwd:
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Mot de passe incorrect")
        st.stop()

# ── Données ────────────────────────────────────────────────────────────────
dates       = list_brief_dates()
alert_dates = list_alert_dates()

total_alerts = sum(
    len((load_alerts(d) or {}).get("alerts", []))
    for d in alert_dates[:30]
)

# ── Sidebar ────────────────────────────────────────────────────────────────
sidebar_brand()

# Status pipeline
if dates:
    last_date = dates[0]
    try:
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        today   = datetime.now(_PARIS).date()
        pipeline_ok = last_dt.date() == today or (today - last_dt.date()).days <= 1
    except Exception:
        pipeline_ok = True
    status_badge(pipeline_ok, last_date)

st.sidebar.markdown("---")
st.sidebar.markdown("### Navigation")
st.sidebar.page_link("streamlit_app.py",              label="📰  Brief du jour")
st.sidebar.page_link("pages/1_📅_Historique.py",     label="📅  Historique")
st.sidebar.page_link("pages/2_🔥_Alertes.py",        label="🔥  Alertes intraday")
st.sidebar.page_link("pages/3_🌍_Heatmap.py",        label="🌍  Heatmap deals")
st.sidebar.page_link("pages/4_🔍_Recherche.py",      label="🔍  Recherche")
st.sidebar.page_link("pages/5_📧_Abonnement.py",     label="📧  Abonnement")
st.sidebar.markdown("---")

c1, c2, c3 = st.sidebar.columns(3)
c1.metric("Briefs", len(dates))
c2.metric("Alertes", total_alerts)
c3.metric("Sources", "80+")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div style="font-size:10px;color:rgba(143,175,200,0.55);padding:4px 0;'
    'line-height:1.6">'
    'Généré chaque matin à 08h30<br>'
    'Propulsé par Gemini + RSS'
    '</div>',
    unsafe_allow_html=True,
)

# ── Handle subscription query param (?page=abonnement)
_qp = st.query_params
if _qp.get("page") == "abonnement":
    st.switch_page("pages/5_📧_Abonnement.py")

# ── Hero section ───────────────────────────────────────────────────────────
today_fr = datetime.now(_PARIS).strftime("%A %d %B %Y").capitalize()

st.markdown(
    f'<div style="margin-bottom:4px">'
    f'<span style="font-size:8px;font-weight:700;letter-spacing:3px;'
    f'text-transform:uppercase;color:#C9A84C">Coffee Economics News</span>'
    f'</div>',
    unsafe_allow_html=True,
)
st.title("Daily Finance Brief")
st.markdown(
    f'<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:20px">'
    f'Veille CIB quotidienne · {today_fr}'
    f'</div>',
    unsafe_allow_html=True,
)

if not dates:
    st.markdown(
        '<div style="background:#FFFFFF;border-radius:8px;padding:40px 32px;'
        'text-align:center;border:1px solid #E8EEF5;margin-top:24px">'
        '<div style="font-size:40px;margin-bottom:16px">⏰</div>'
        '<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:20px;'
        'font-weight:700;color:#071828;margin-bottom:10px">Premier brief bientôt disponible</div>'
        '<div style="font-size:14px;color:#6B7A8E;line-height:1.6">'
        'Le pipeline se déclenche automatiquement à <strong>08h30 Paris</strong>.<br>'
        'Les briefs seront affichés ici dès la première génération.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ── Sélecteur d'édition ────────────────────────────────────────────────────
dcol1, dcol2 = st.columns([3, 1])
with dcol1:
    selected_date = st.selectbox(
        "Édition du brief",
        options=dates,
        index=0,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
        label_visibility="collapsed",
    )
with dcol2:
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.caption(f"{len(dates)} édition{'s' if len(dates) > 1 else ''} archivée{'s' if len(dates) > 1 else ''}")

brief  = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news   = brief.get("news", [])
stats  = brief.get("stats", {})
market = brief.get("market_snapshot", {})

# ── Market snapshot ────────────────────────────────────────────────────────
if market:
    st.markdown("---")
    section_header("Marchés")
    cols = st.columns(len(market))
    TREND = {"up": "#059669", "down": "#DC2626", "flat": "#9CA3AF"}
    ARROW = {"up": "▲", "down": "▼", "flat": "─"}
    for col, (label, data) in zip(cols, market.items()):
        trend  = data.get("trend", "flat")
        color  = TREND.get(trend, "#9CA3AF")
        arrow  = ARROW.get(trend, "─")
        change = data.get("change", "")
        unit   = f' <span style="font-size:10px;color:#B0BAC7">{data["unit"]}</span>' if data.get("unit") else ""
        col.markdown(
            f'<div style="background:#FFFFFF;border-radius:6px;padding:14px 16px 12px;'
            f'border:1px solid #E8EEF5;box-shadow:0 1px 3px rgba(11,37,69,0.04)">'
            f'<div style="font-size:7.5px;font-weight:700;letter-spacing:1.5px;'
            f'text-transform:uppercase;color:#9CA3AF;margin-bottom:6px">{label}</div>'
            f'<div style="font-family:\'Playfair Display\',Georgia,serif;'
            f'font-size:21px;font-weight:700;color:#071828;letter-spacing:-0.5px;'
            f'line-height:1">{data.get("value","—")}{unit}</div>'
            f'<div style="font-size:11px;font-weight:600;color:{color};margin-top:5px">'
            f'{arrow} {change or "—"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Métadonnées brief ──────────────────────────────────────────────────────
st.markdown("---")
_gen = brief.get("generated_at", "")
_gen_display = f"{_gen[:10]} à {_gen[11:16]}" if len(_gen) >= 16 else _gen[:10]
_has_analysis = sum(1 for n in news if (n.get("so_what") or "").strip() and "[Analyse LLM indisponible" not in (n.get("so_what") or ""))

mcol1, mcol2, mcol3 = st.columns(3)
with mcol1:
    st.metric("News sélectionnées", len(news))
with mcol2:
    st.metric("Avec analyse Gemini", _has_analysis)
with mcol3:
    st.metric("Sources scannées", stats.get("collected", "—"))

if brief.get("low_volume"):
    st.warning("⚠ Volume réduit — seules les news les plus pertinentes ont été retenues ce jour.")

st.caption(f"Généré le {_gen_display} · {stats.get('collected', '?')} sources scannées")

# ── Filtres ────────────────────────────────────────────────────────────────
cats_present    = sorted({item.get("category", "Sector") for item in news})
cat_options     = {CATEGORY_LABELS.get(c, c): c for c in cats_present}
sectors_present = sorted({item.get("sector", "Other") for item in news})

# Reset guard
if st.session_state.get("_reset_filters"):
    for k in ["main_region", "main_cat", "main_sector"]:
        st.session_state.pop(k, None)
    st.session_state.pop("_reset_filters", None)

st.markdown("---")
with st.expander("🔧 Filtres", expanded=False):
    fcol1, fcol2, fcol3, fcol_reset = st.columns([1, 1, 1, 0.3])
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
        st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
        if st.button("↺", help="Réinitialiser tous les filtres", use_container_width=True):
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

section_header(
    f"{len(filtered_news)} news{'  · filtré' if _filters_active else ''}"
)

# ── News cards ─────────────────────────────────────────────────────────────
if not filtered_news:
    st.info("Aucune news ne correspond aux filtres sélectionnés.")
else:
    for item in filtered_news:
        news_card(item)

# ── Exports ────────────────────────────────────────────────────────────────
st.markdown("---")
col_csv, col_bb, col_info = st.columns([1, 1, 2])

with col_csv:
    if news:
        import json as _json
        news_json = _json.dumps(news, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇ Export JSON",
            data=news_json,
            file_name=f"brief_{selected_date}.json",
            mime="application/json",
            help="Export brut JSON de l'édition",
        )

with col_bb:
    if news:
        st.download_button(
            "⬇ Bloomberg CSV",
            data=_build_bloomberg_csv(news, selected_date),
            file_name=f"bloomberg_{selected_date}.csv",
            mime="text/csv",
            help="Format compatible Bloomberg Terminal / Excel deal tracker",
        )

with col_info:
    st.caption(
        f"Brief du {selected_date} · {len(news)} news "
        f"· {len(filtered_news)} affichées"
    )
