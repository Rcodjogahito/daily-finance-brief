"""Page 2 — Alertes chaudes."""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.archiver import list_alert_dates, load_alerts
from src.styles import inject_css, sidebar_brand, page_toolbar

st.set_page_config(page_title="Alertes — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()

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

page_toolbar()

st.markdown(
    '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Alertes intraday")

dates = list_alert_dates()
if not dates:
    st.info("Aucune alerte déclenchée pour le moment.")
    st.stop()

all_alerts: list[dict] = []
for d in dates[:90]:
    data = load_alerts(d)
    if data:
        for alert in data.get("alerts", []):
            alert["_date"] = d
            all_alerts.append(alert)

with st.sidebar:
    st.markdown("### Filtres")
    alert_types    = ["MEGA_DEAL", "FALLEN_ANGEL", "PROFIT_WARNING"]
    selected_types = st.multiselect("Type", alert_types, default=alert_types)
    period = st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "Tout"], index=1)

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
c1.metric("Total",          len(filtered_alerts))
c2.metric("Mega deals",     sum(1 for a in filtered_alerts if "MEGA_DEAL"      in get_types(a)))
c3.metric("Fallen angels",  sum(1 for a in filtered_alerts if "FALLEN_ANGEL"   in get_types(a)))
c4.metric("Profit warnings",sum(1 for a in filtered_alerts if "PROFIT_WARNING" in get_types(a)))

# ── Chart ──────────────────────────────────────────────────────────────────
if filtered_alerts:
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
        height=260,
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=0, r=0),
        legend_title_text="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter, Helvetica Neue, Arial, sans-serif",
        font_color="#374151",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#F3F4F6", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f'<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:16px">{len(filtered_alerts)} alertes</div>', unsafe_allow_html=True)

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

    headline = alert.get("headline", alert.get("title", ""))
    deal_str = ""
    if alert.get("deal_size_eur"):
        deal_str = f' <span style="background:#EBF2FF;color:#0B1D2E;padding:2px 6px;border-radius:2px;font-size:10px;font-weight:700">{alert["deal_size_eur"]/1e9:.1f} Md€</span>'

    meta_parts = [alert.get("source", ""), alert.get("_date", ""), alert.get("geography", ""), alert.get("sector", "")]
    sep = ' <span style="color:#D1D5DB">·</span> '
    meta = sep.join(p for p in meta_parts if p)

    url = alert.get("url", "")

    with st.container():
        st.markdown(
            f'<div style="padding:16px 0 8px">'
            f'<span style="background:{color};color:#fff;padding:2px 7px;border-radius:2px;'
            f'font-size:9px;font-weight:700;letter-spacing:0.7px;text-transform:uppercase">{label}</span>'
            f'{deal_str}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<a href="{url}" target="_blank" style="font-size:16px;font-weight:700;'
            f'color:#0B1D2E;text-decoration:none;display:block;margin-bottom:5px">{headline}</a>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:11px;color:#9CA3AF;margin-bottom:10px">{meta}</div>',
            unsafe_allow_html=True,
        )

        # Alert reason — always visible
        if areason:
            st.markdown(
                f'<div style="font-size:12px;color:#7F1D1D;font-weight:600;'
                f'background:#FEF2F2;border:1px solid #FECACA;border-radius:2px;'
                f'padding:6px 10px;margin-bottom:10px">{areason}</div>',
                unsafe_allow_html=True,
            )

        # Summary — always visible
        if alert.get("summary"):
            st.markdown(
                f'<div style="font-size:13.5px;line-height:1.7;color:#374151;margin-bottom:10px">{alert.get("summary","")}</div>',
                unsafe_allow_html=True,
            )

        # Analyse d'impact — always visible, prominent
        so_what = alert.get("so_what", "")
        if so_what:
            st.markdown(
                f'<div style="background:#FEF9F5;border-left:3px solid {color};'
                f'padding:12px 16px;border-radius:0 3px 3px 0;margin-bottom:10px">'
                f'<span style="font-size:8px;font-weight:700;letter-spacing:2px;'
                f'text-transform:uppercase;color:{color};display:block;margin-bottom:7px">'
                f'Analyse d\'impact &amp; conséquences</span>'
                f'<span style="font-size:13px;line-height:1.7;color:#1E1E1E">{so_what}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#F9FAFB;border-left:3px solid #D1D5DB;'
                'padding:10px 14px;border-radius:0 3px 3px 0;margin-bottom:10px">'
                '<span style="font-size:11px;color:#9CA3AF;font-style:italic">'
                'Analyse d\'impact en cours de génération.</span>'
                '</div>',
                unsafe_allow_html=True,
            )

        if url:
            st.markdown(
                f'<a href="{url}" target="_blank" style="font-size:12px;color:#1565C0;font-weight:500;text-decoration:none">Lire l\'article source</a>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="border-top:1px solid #E9ECF0;margin-top:12px"></div>', unsafe_allow_html=True)
