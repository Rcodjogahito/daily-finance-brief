"""Page 1 — Historique calendar picker."""
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.archiver import list_brief_dates, load_brief

st.set_page_config(page_title="Historique — Daily Finance Brief", page_icon="📅", layout="wide")

CATEGORY_COLORS = {
    "M&A": "#16A34A", "LevFin": "#EA580C", "Energy": "#7C3AED",
    "Credit": "#2563EB", "Macro": "#475569", "Geo": "#DC2626",
    "Reg": "#CA8A04", "Sector": "#0891B2",
}


def category_badge(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#64748b")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;font-weight:700">{cat}</span>'


st.title("📅 Historique des briefs")

dates = list_brief_dates()
if not dates:
    st.warning("Aucun brief archivé.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.markdown("### Filtres")
    selected_date = st.selectbox(
        "Date",
        options=dates,
        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize(),
    )

    all_cats = ["M&A", "LevFin", "Energy", "Credit", "Macro", "Geo", "Reg", "Sector"]
    selected_cats = st.multiselect("Catégories", all_cats, default=all_cats)

    all_sectors = ["Energy", "Financials", "Healthcare", "TMT", "Industrials",
                   "Aviation", "Defense", "Consumer", "Luxury", "Entertainment",
                   "Real Estate", "Materials", "Services", "Other"]
    selected_sectors = st.multiselect("Secteurs", all_sectors, default=all_sectors)

    all_geos = ["France", "UK", "Germany", "Italy", "Spain", "Nordics", "Benelux",
                "Other Europe", "USA", "Canada", "MENA", "Africa", "Asia", "LatAm", "Global"]
    selected_geos = st.multiselect("Géographies", all_geos, default=all_geos)

brief = load_brief(selected_date)
if not brief:
    st.error(f"Brief du {selected_date} introuvable.")
    st.stop()

news = brief.get("news", [])

# Apply filters
filtered = [
    n for n in news
    if n.get("category", "Sector") in selected_cats
    and n.get("sector", "Other") in selected_sectors
    and n.get("geography", "Global") in selected_geos
]

# Header
date_fmt = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A %d %B %Y").capitalize()
st.subheader(f"{date_fmt} — {len(filtered)} news")

stats = brief.get("stats", {})
c1, c2, c3 = st.columns(3)
c1.metric("Collectées", stats.get("collected", "—"))
c2.metric("Sélectionnées", len(news))
c3.metric("Affichées", len(filtered))

if not filtered:
    st.info("Aucune news ne correspond aux filtres sélectionnés.")
    st.stop()

st.markdown("---")

# Render news cards
for item in filtered:
    deal = f" **{item['deal_size_eur']/1e9:.1f} Md€**" if item.get("deal_size_eur") else ""
    multi = f" ✓ {item['source_count']} sources" if item.get("source_count", 1) >= 2 else ""

    with st.container():
        col_r, col_c = st.columns([1, 11])
        with col_r:
            st.markdown(f"<div style='font-size:24px;font-weight:900;color:#0A1F44'>#{item.get('rank','')}</div>", unsafe_allow_html=True)
        with col_c:
            st.markdown(
                f"{category_badge(item.get('category','Sector'))}{deal}<span style='color:#16A34A;font-size:12px'>{multi}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"#### [{item.get('headline', item.get('title',''))}]({item.get('url','')})")
            st.caption(f"📰 {item.get('source','')} &nbsp;|&nbsp; 📍 {item.get('geography','')} &nbsp;|&nbsp; 🏭 {item.get('sector','')}")
            st.markdown(item.get("summary", ""))
            st.info(f"💡 **So what** — {item.get('so_what', '')}")
        st.markdown("---")

# PDF Export
if st.button("📥 Exporter ce brief en PDF"):
    try:
        from xhtml2pdf import pisa
        from jinja2 import Environment, FileSystemLoader
        import io

        template_dir = Path(__file__).parent.parent / "src" / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        template = env.get_template("email_brief.html")
        html = template.render(
            brief=brief,
            streamlit_url="",
            generated_at=datetime.now().strftime("%d/%m/%Y"),
        )
        pdf_buf = io.BytesIO()
        pisa.CreatePDF(html, dest=pdf_buf)
        st.download_button(
            "⬇️ Télécharger PDF",
            data=pdf_buf.getvalue(),
            file_name=f"brief_{selected_date}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Erreur PDF : {e}")
