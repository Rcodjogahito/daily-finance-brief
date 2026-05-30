"""Page 2 — Alertes chaudes intraday."""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.archiver import list_alert_dates, load_alerts
from src.styles import inject_all, sidebar_nav, section_header, _is_real_so_what

st.set_page_config(
    page_title="Alertes — Daily Finance Brief",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_all()
sidebar_nav()

ALERT_COLORS = {
    "MEGA_DEAL":      "#1A5F8C",
    "FALLEN_ANGEL":   "#8B1A2E",
    "PROFIT_WARNING": "#9C6000",
}
ALERT_LABELS = {
    "MEGA_DEAL":      "Mega Deal",
    "FALLEN_ANGEL":   "Fallen Angel",
    "PROFIT_WARNING": "Profit Warning",
}
ALERT_ICONS = {
    "MEGA_DEAL":      "🏦",
    "FALLEN_ANGEL":   "📉",
    "PROFIT_WARNING": "⚠️",
}

# ── Sidebar — filtres page ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres")
    alert_types    = ["MEGA_DEAL", "FALLEN_ANGEL", "PROFIT_WARNING"]
    selected_types = st.multiselect("Type", alert_types, default=alert_types,
                                    format_func=lambda t: ALERT_LABELS.get(t, t))
    period = st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "Tout"], index=1)

# ── Header ─────────────────────────────────────────────────────────────────
section_header("Coffee Economics News")
st.title("Alertes intraday")
st.markdown(
    '<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:20px">'
    'Mega deals, Fallen angels, Profit warnings détectés en temps réel'
    '</div>',
    unsafe_allow_html=True,
)

# ── Load data ──────────────────────────────────────────────────────────────
dates = list_alert_dates()
if not dates:
    st.markdown(
        '<div style="background:#FFFFFF;border-radius:8px;padding:40px 32px;'
        'text-align:center;border:1px solid #E8EEF5;margin-top:24px">'
        '<div style="font-size:40px;margin-bottom:16px">🔔</div>'
        '<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:20px;'
        'font-weight:700;color:#071828;margin-bottom:10px">Aucune alerte pour le moment</div>'
        '<div style="font-size:14px;color:#6B7A8E">'
        'Les alertes intraday (Mega Deal, Fallen Angel, Profit Warning) '
        'apparaîtront ici dès leur détection.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

all_alerts: list[dict] = []
for d in dates[:90]:
    data = load_alerts(d)
    if data:
        for alert in data.get("alerts", []):
            alert["_date"] = d
            all_alerts.append(alert)

cutoff = {
    "7 derniers jours":  (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
    "30 derniers jours": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
    "Tout":              "2000-01-01",
}[period]


def get_types(alert: dict) -> list[str]:
    return [f.get("type", "") for f in alert.get("alert_flags", [])]


filtered_alerts = [
    a for a in all_alerts
    if a.get("_date", "") >= cutoff
    and any(t in selected_types for t in get_types(a))
]

# ── Stats ──────────────────────────────────────────────────────────────────
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total alertes",    len(filtered_alerts))
c2.metric("🏦 Mega deals",   sum(1 for a in filtered_alerts if "MEGA_DEAL"      in get_types(a)))
c3.metric("📉 Fallen angels", sum(1 for a in filtered_alerts if "FALLEN_ANGEL"   in get_types(a)))
c4.metric("⚠ Profit warnings",sum(1 for a in filtered_alerts if "PROFIT_WARNING" in get_types(a)))

# ── Chart ──────────────────────────────────────────────────────────────────
if filtered_alerts:
    st.markdown("---")
    df = pd.DataFrame([
        {"date": a.get("_date", ""), "type": get_types(a)[0] if get_types(a) else "UNKNOWN"}
        for a in filtered_alerts
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    weekly = df.groupby(["week", "type"]).size().reset_index(name="count")

    fig = px.bar(
        weekly, x="week", y="count", color="type",
        color_discrete_map=ALERT_COLORS,
        labels={"week": "", "count": "Alertes", "type": "Type"},
        height=240,
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=0, r=0),
        legend_title_text="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter, Helvetica Neue, Arial, sans-serif",
        font_color="#374151",
        font_size=11,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#F3F4F6", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
section_header(f"{len(filtered_alerts)} alertes")

if not filtered_alerts:
    st.info("Aucune alerte dans la période sélectionnée.")
    st.stop()

# ── Alert cards ────────────────────────────────────────────────────────────
for alert in sorted(filtered_alerts, key=lambda a: a.get("_date", ""), reverse=True):
    flags   = alert.get("alert_flags", [{}])
    atype   = flags[0].get("type", "ALERT") if flags else "ALERT"
    areason = flags[0].get("reason", "") if flags else ""
    color   = ALERT_COLORS.get(atype, "#374151")
    label   = ALERT_LABELS.get(atype, atype.replace("_", " "))
    icon    = ALERT_ICONS.get(atype, "🔔")

    headline = alert.get("headline", alert.get("title", ""))
    deal_str = ""
    if alert.get("deal_size_eur"):
        deal_str = (
            f' <span style="display:inline-block;background:#EBF4FF;color:#0B2545;'
            f'padding:2px 8px;border-radius:2px;font-size:9px;font-weight:700;'
            f'margin-left:6px">{alert["deal_size_eur"]/1e9:.1f}&nbsp;Md€</span>'
        )

    meta_parts = [alert.get("source", ""), alert.get("_date", ""),
                  alert.get("geography", ""), alert.get("sector", "")]
    sep = ' <span style="color:#D1D5DB">·</span> '
    meta = sep.join(
        f'<span style="color:#9CA3AF">{p}</span>' for p in meta_parts if p
    )
    url = alert.get("url", "")
    _sw_raw = (alert.get("so_what", "") or "").strip()
    so_what = _sw_raw if _is_real_so_what(_sw_raw) else ""

    st.markdown(
        f'<div style="background:#FFFFFF;border-left:4px solid {color};'
        f'padding:20px 24px 18px;margin-bottom:12px;border-radius:0 6px 6px 0;'
        f'box-shadow:0 2px 8px rgba(11,37,69,0.06),0 0 0 1px rgba(11,37,69,0.04)">'

        # Type badge
        f'<div style="margin-bottom:12px">'
        f'<span style="background:{color};color:#fff;padding:3px 9px;border-radius:2px;'
        f'font-size:9px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase">'
        f'{icon} {label}</span>'
        f'{deal_str}'
        f'</div>'

        # Headline
        + (f'<a href="{url}" target="_blank" style="'
           f'font-family:\'Playfair Display\',Georgia,serif;font-size:16.5px;font-weight:700;'
           f'color:#071828;text-decoration:none;display:block;margin-bottom:6px;line-height:1.38">'
           f'{headline}</a>'
           if url else
           f'<div style="font-family:\'Playfair Display\',Georgia,serif;font-size:16.5px;'
           f'font-weight:700;color:#071828;margin-bottom:6px;line-height:1.38">{headline}</div>')

        # Meta
        + f'<div style="font-size:10.5px;color:#9CA3AF;margin-bottom:12px">{meta}</div>'

        # Alert reason
        + (f'<div style="font-size:12px;color:#7F1D1D;font-weight:600;'
           f'background:#FEF2F2;border:1px solid #FECACA;border-radius:3px;'
           f'padding:7px 11px;margin-bottom:12px">{areason}</div>'
           if areason else "")

        # Summary
        + (f'<div style="font-size:13.5px;line-height:1.8;color:#374151;margin-bottom:12px">'
           f'{alert.get("summary","")}</div>'
           if alert.get("summary") else "")

        # So what
        + (f'<div style="background:linear-gradient(135deg,#FAFBFD 0%,#F8F9FC 100%);'
           f'border-left:3px solid {color};padding:14px 18px 12px;'
           f'border-radius:0 4px 4px 0;'
           f'box-shadow:inset 0 0 0 1px rgba(11,37,69,0.06)">'
           f'<div style="font-size:7.5px;font-weight:700;letter-spacing:2.5px;'
           f'text-transform:uppercase;color:{color};margin-bottom:9px">'
           f'Analyse d\'impact &amp; conséquences</div>'
           f'<div style="font-size:13px;line-height:1.8;color:#1E3A5F">{so_what}</div>'
           f'</div>'
           if so_what else
           f'<div style="background:#F9FAFB;border-left:3px solid #D1D5DB;'
           f'padding:10px 14px;border-radius:0 3px 3px 0">'
           f'<span style="font-size:11px;color:#9CA3AF;font-style:italic">'
           f'Analyse d\'impact en cours de génération.</span></div>')

        # Read link
        + (f'<div style="margin-top:14px">'
           f'<a href="{url}" target="_blank" style="font-size:11px;color:#0B2545;'
           f'font-weight:600;text-decoration:none;letter-spacing:0.02em;'
           f'border-bottom:1px solid rgba(11,37,69,0.2);padding-bottom:1px">'
           f'Lire l\'article &#8594;</a></div>'
           if url else "")

        + '</div>',
        unsafe_allow_html=True,
    )
