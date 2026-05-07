"""Page 1 — Historique."""
import io
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.archiver import list_brief_dates, load_brief
from src.styles import inject_css, sidebar_brand, news_card

st.set_page_config(page_title="Historique — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()

st.markdown(
    '<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#9CA3AF;margin-bottom:4px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Historique des briefs")

dates = list_brief_dates()
if not dates:
    st.warning("Aucun brief archivé.")
    st.stop()

with st.sidebar:
    st.markdown("### Filtres")
    selected_date = st.selectbox(
        "Date",
        options=dates,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
    )
    all_cats = ["M&A", "LevFin", "Energy", "Credit", "Macro", "Geo", "Reg", "Sector"]
    selected_cats = st.multiselect("Catégories", all_cats, default=all_cats)
    all_sectors = [
        "Energy", "Financials", "Healthcare", "TMT", "Industrials",
        "Aviation", "Defense", "Consumer", "Luxury", "Entertainment",
        "Real Estate", "Materials", "Services", "Other",
    ]
    selected_sectors = st.multiselect("Secteurs", all_sectors, default=all_sectors)
    all_geos = [
        "France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux",
        "Other Europe", "USA", "Canada", "MENA", "Africa", "Asia", "LatAm", "Global",
    ]
    selected_geos = st.multiselect("Géographies", all_geos, default=all_geos)

brief = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news     = brief.get("news", [])
filtered = [
    n for n in news
    if n.get("category", "Sector") in selected_cats
    and n.get("sector", "Other") in selected_sectors
    and n.get("geography", "Global") in selected_geos
]

date_fmt = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize()
st.markdown(f'<div style="color:#6B7A8E;font-size:13px;margin-bottom:16px">{date_fmt} &nbsp;·&nbsp; {len(filtered)} news</div>', unsafe_allow_html=True)

s = brief.get("stats", {})
c1, c2, c3 = st.columns(3)
c1.metric("Collectées", s.get("collected", "—"))
c2.metric("Sélectionnées", len(news))
c3.metric("Affichées", len(filtered))

if not filtered:
    st.info("Aucune news ne correspond aux filtres sélectionnés.")
    st.stop()

st.markdown("---")

for item in filtered:
    news_card(item)

# PDF Export
st.markdown("---")
if st.button("Export PDF"):
    try:
        from xhtml2pdf import pisa
        from jinja2 import Environment, FileSystemLoader

        template_dir = Path(__file__).parent.parent / "src" / "templates"
        env  = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        html = env.get_template("email_brief.html").render(
            brief=brief,
            streamlit_url="",
            generated_at=datetime.now().strftime("%d/%m/%Y"),
        )
        pdf_buf = io.BytesIO()
        pisa.CreatePDF(html, dest=pdf_buf)
        st.download_button(
            "Télécharger le PDF",
            data=pdf_buf.getvalue(),
            file_name=f"brief_{selected_date}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Erreur PDF : {e}")
