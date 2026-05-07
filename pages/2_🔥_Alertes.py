"""Page 2 — Alertes chaudes."""
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.archiver import list_alert_dates, load_alerts

st.set_page_config(page_title="Alertes — Daily Finance Brief", page_icon="🔥", layout="wide")

ALERT_COLORS = {
    "MEGA_DEAL": "#16A34A",
    "FALLEN_ANGEL": "#DC2626",
    "PROFIT_WARNING": "#EA580C",
}

ALERT_ICONS = {
    "MEGA_DEAL": "💰",
    "FALLEN_ANGEL": "👼",
    "PROFIT_WARNING": "⚠️",
}

st.title("🔥 Alertes chaudes intraday")

dates = list_alert_dates()
if not dates:
    st.info("Aucune alerte déclenchée pour le moment.")
    st.stop()

# Load all alerts from last 90 days for stats
all_alerts: list[dict] = []
for d in dates[:90]:
    data = load_alerts(d)
    if data:
        for alert in data.get("alerts", []):
            alert["_date"] = d
            all_alerts.append(alert)

# Sidebar filters
with st.sidebar:
    st.markdown("### Filtres")
    alert_types = ["MEGA_DEAL", "FALLEN_ANGEL", "PROFIT_WARNING"]
    selected_types = st.multiselect("Type d'alerte", alert_types, default=alert_types)

    period = st.selectbox("Période", ["7 derniers jours", "30 derniers jours", "Tout"], index=1)
    if period == "7 derniers jours":
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "30 derniers jours":
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        cutoff = "2000-01-01"

# Filter alerts
def get_alert_types(alert: dict) -> list[str]:
    return [f.get("type", "") for f in alert.get("alert_flags", [])]

filtered_alerts = [
    a for a in all_alerts
    if a.get("_date", "") >= cutoff
    and any(t in selected_types for t in get_alert_types(a))
]

# Stats
st.markdown("### Statistiques")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total alertes (filtrées)", len(filtered_alerts))
c2.metric("Mega deals", sum(1 for a in filtered_alerts if "MEGA_DEAL" in get_alert_types(a)))
c3.metric("Fallen angels", sum(1 for a in filtered_alerts if "FALLEN_ANGEL" in get_alert_types(a)))
c4.metric("Profit warnings", sum(1 for a in filtered_alerts if "PROFIT_WARNING" in get_alert_types(a)))

# Weekly evolution chart
if filtered_alerts:
    df = pd.DataFrame([
        {
            "date": a.get("_date", ""),
            "type": get_alert_types(a)[0] if get_alert_types(a) else "UNKNOWN",
        }
        for a in filtered_alerts
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    weekly = df.groupby(["week", "type"]).size().reset_index(name="count")

    fig = px.bar(
        weekly, x="week", y="count", color="type",
        color_discrete_map=ALERT_COLORS,
        title="Évolution hebdomadaire des alertes",
        labels={"week": "Semaine", "count": "Nb alertes", "type": "Type"},
        height=300,
    )
    fig.update_layout(margin=dict(t=40, b=20), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(f"### {len(filtered_alerts)} alertes")

if not filtered_alerts:
    st.info("Aucune alerte dans la période sélectionnée.")
    st.stop()

# Timeline
for alert in sorted(filtered_alerts, key=lambda a: a.get("_date", ""), reverse=True):
    flags = alert.get("alert_flags", [{}])
    atype = flags[0].get("type", "ALERT") if flags else "ALERT"
    areason = flags[0].get("reason", "") if flags else ""
    color = ALERT_COLORS.get(atype, "#64748b")
    icon = ALERT_ICONS.get(atype, "🔔")

    with st.container():
        st.markdown(
            f'<div style="border-left:4px solid {color};padding:12px 16px;margin-bottom:12px;background:#fafafa;border-radius:0 6px 6px 0">'
            f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700">{icon} {atype}</span>'
            f'&nbsp;<span style="font-size:12px;color:#64748b">{alert.get("_date","")}</span><br>'
            f'<strong style="font-size:15px">{alert.get("headline", alert.get("title",""))}</strong><br>'
            f'<span style="font-size:12px;color:#64748b">📰 {alert.get("source","")} &nbsp; 📍 {alert.get("geography","")} &nbsp; 🏭 {alert.get("sector","")}</span><br>'
            f'<em style="font-size:12px;color:#991B1B">{areason}</em>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Voir détails + So what"):
            st.markdown(alert.get("summary", ""))
            if alert.get("so_what"):
                st.info(f"💡 **So what** — {alert['so_what']}")
            if alert.get("deal_size_eur"):
                st.metric("Montant", f"{alert['deal_size_eur']/1e9:.1f} Md€")
            st.markdown(f"[→ Lire l'article source]({alert.get('url', '')})")
