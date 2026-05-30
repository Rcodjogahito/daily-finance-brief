"""Shared Streamlit CSS and UI helpers — Daily Finance Brief design system.

Design language: Investment-bank quality (Morgan Stanley / Goldman Sachs tier)
  - Fonts: Playfair Display (700/800) for headings; Inter for body
  - Primary navy: #0B2545
  - Accent gold: #C9A84C
  - Background: #F4F6FA
  - Cards: white with subtle shadow and category left-border
"""
import streamlit as st

CATEGORY_COLORS = {
    "M&A":         "#1A5F8C",
    "LevFin":      "#9C6000",
    "Energy":      "#5B21B6",
    "Credit":      "#1E40AF",
    "Macro":       "#374151",
    "Geo":         "#8B1A2E",
    "Reg":         "#78350F",
    "Sector":      "#0C6E85",
    "Nominations": "#4B5563",
    "Banking":     "#0C3B6E",
}

CATEGORY_LABELS = {
    "M&A":         "Deals & M&A",
    "LevFin":      "Leveraged Finance",
    "Energy":      "Énergie",
    "Credit":      "Crédit & Ratings",
    "Macro":       "Macroéconomie",
    "Geo":         "Géopolitique",
    "Reg":         "Régulation",
    "Sector":      "Actualité sectorielle",
    "Nominations": "Nominations",
    "Banking":     "Actualité bancaire",
}

ALL_CATEGORIES = list(CATEGORY_COLORS.keys())

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,800;1,700&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & globals ──────────────────────────────── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] * {
    font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="manage-app-button"],
header { display: none !important; }

/* ── App background ─────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background-color: #F4F6FA !important;
}
[data-testid="stAppViewContainer"] > .main {
    background-color: #F4F6FA !important;
}
.main .block-container {
    padding: 1.5rem 2.5rem 3rem !important;
    max-width: 1080px !important;
}

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07192E 0%, #0B2545 40%, #0E2D57 100%) !important;
    border-right: 1px solid rgba(201,168,76,0.15) !important;
    min-width: 230px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] * { color: #8FAFC8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #C9D8E8 !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] a {
    color: #7FAACC !important;
    text-decoration: none !important;
}
[data-testid="stSidebar"] a:hover { color: #C9A84C !important; }
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid rgba(201,168,76,0.12) !important;
    margin: 0.6rem 0 !important;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #EEF5FF !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    color: #4A7FA5 !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Sidebar nav links ──────────────────────────── */
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    display: flex !important;
    align-items: center !important;
    padding: 8px 12px !important;
    border-radius: 4px !important;
    border-left: 2px solid transparent !important;
    color: #7FAACC !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    margin: 1px 0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    border-left-color: #C9A84C !important;
    color: #EEF5FF !important;
    background: rgba(201,168,76,0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"].active a {
    border-left-color: #C9A84C !important;
    color: #F0F8FF !important;
    background: rgba(201,168,76,0.12) !important;
    font-weight: 600 !important;
}

/* ── Typography ─────────────────────────────────── */
h1 {
    font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: #071828 !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
    margin-bottom: 0.1rem !important;
}
h2 {
    font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #0B2545 !important;
    letter-spacing: -0.3px !important;
}
h3 {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #374151 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Overline label ─────────────────────────────── */
.overline {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #C9A84C;
    margin-bottom: 6px;
    display: block;
}

/* ── Metrics ────────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    color: #071828 !important;
    letter-spacing: -0.5px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.6rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Metric cards background ────────────────────── */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border-radius: 6px !important;
    padding: 14px 18px !important;
    border: 1px solid #E8EEF5 !important;
    box-shadow: 0 1px 4px rgba(11,37,69,0.05) !important;
}

/* ── Buttons ────────────────────────────────────── */
.stButton > button {
    background: #0B2545 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    font-size: 0.73rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.2rem !important;
    transition: background 0.15s ease !important;
}
.stButton > button:hover {
    background: #1A3A5C !important;
    transform: none !important;
}
.stButton > button:active {
    background: #071828 !important;
}
.stDownloadButton > button {
    background: transparent !important;
    color: #0B2545 !important;
    border: 1.5px solid #0B2545 !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    font-size: 0.73rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    transition: all 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #0B2545 !important;
    color: #FFFFFF !important;
}

/* ── Form controls ──────────────────────────────── */
.stSelectbox label, .stMultiSelect label,
.stRadio label, .stTextInput label,
.stDateInput label, .stTextArea label {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
    margin-bottom: 4px !important;
}

/* ── Select / Input borders ─────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] {
    border-color: #D8E2EE !important;
    border-radius: 4px !important;
    background: #FFFFFF !important;
}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"] > div:focus-within {
    border-color: #0B2545 !important;
    box-shadow: 0 0 0 2px rgba(11,37,69,0.12) !important;
}

/* ── Multiselect tags ───────────────────────────── */
[data-baseweb="tag"] {
    background-color: #E8EFF8 !important;
    color: #0B2545 !important;
    border-radius: 3px !important;
    font-size: 10.5px !important;
    font-weight: 600 !important;
    height: 21px !important;
    line-height: 21px !important;
    padding: 0 6px !important;
    margin: 2px !important;
}
[data-baseweb="tag"] svg { fill: #0B2545 !important; }

/* ── Info / Warning / Error ─────────────────────── */
[data-testid="stAlert"] {
    border-radius: 4px !important;
    font-size: 0.84rem !important;
    border: none !important;
}
[data-testid="stInfo"] {
    background: #EEF4FF !important;
    border-left: 3px solid #0B2545 !important;
    color: #1E3A5F !important;
}
[data-testid="stWarning"] {
    background: #FFFBF0 !important;
    border-left: 3px solid #C9A84C !important;
}
[data-testid="stSuccess"] {
    background: #F0FAF4 !important;
    border-left: 3px solid #059669 !important;
}
[data-testid="stError"] {
    background: #FFF5F5 !important;
    border-left: 3px solid #DC2626 !important;
}

/* ── Expander ───────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F2 !important;
    border-radius: 6px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(11,37,69,0.04) !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    background: #F8FAFD !important;
    padding: 11px 16px !important;
    border-radius: 6px !important;
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    color: #374151 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
}
[data-testid="stExpander"] summary:hover {
    background: #EDF1F8 !important;
}
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    padding: 16px !important;
    background: #FFFFFF !important;
}
details summary { cursor: pointer !important; }

/* ── Caption ────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.73rem !important;
    color: #9CA3AF !important;
    letter-spacing: 0.02em !important;
}

/* ── Divider ────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #E8EEF5 !important;
    margin: 1rem 0 !important;
}

/* ── Tabs ───────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #E8EEF5 !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
    padding: 8px 16px !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    background: transparent !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #0B2545 !important;
    border-bottom-color: #C9A84C !important;
}

/* ── Spinner ────────────────────────────────────── */
[data-testid="stSpinner"] {
    color: #0B2545 !important;
}

/* ── Scrollbar ──────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F4F6FA; }
::-webkit-scrollbar-thumb { background: #CBD5E0; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── Responsive: tablette ───────────────────────── */
@media (max-width: 900px) {
    .main .block-container {
        padding: 1rem 1.2rem 2rem !important;
    }
    h1 { font-size: 1.6rem !important; }
}
</style>
"""

# ── Sidebar brand ──────────────────────────────────────────────────────────
_SIDEBAR_BRAND_HTML = """
<div style="padding:20px 16px 16px;border-bottom:1px solid rgba(201,168,76,0.15);margin-bottom:8px">
  <div style="font-size:7.5px;font-weight:700;letter-spacing:3.5px;text-transform:uppercase;
              color:#C9A84C;margin-bottom:10px;opacity:0.9">
    Coffee Economics News
  </div>
  <div style="font-family:'Playfair Display',Georgia,serif;font-size:19px;font-weight:800;
              color:#EEF5FF;letter-spacing:-0.5px;line-height:1.25">
    Daily Finance<br>Brief
  </div>
  <div style="margin-top:8px;font-size:10px;color:rgba(143,175,200,0.7);letter-spacing:0.05em">
    CIB Intelligence Platform
  </div>
</div>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


inject_all = inject_css  # alias pour compat pages


def sidebar_brand() -> None:
    st.sidebar.markdown(_SIDEBAR_BRAND_HTML, unsafe_allow_html=True)


def overline(text: str, color: str = "#C9A84C", spacing: str = "3px") -> str:
    """Return an HTML overline label string."""
    return (
        f'<div style="font-size:8px;font-weight:700;letter-spacing:{spacing};'
        f'text-transform:uppercase;color:{color};margin-bottom:8px">{text}</div>'
    )


def section_header(label: str) -> None:
    """Render a gold overline section label."""
    st.markdown(overline(label), unsafe_allow_html=True)


def status_badge(pipeline_ok: bool, last_date: str) -> None:
    """Render a small pipeline health badge in the sidebar."""
    color = "#059669" if pipeline_ok else "#DC2626"
    dot = "●"
    status_text = f"Actif · {last_date}" if pipeline_ok else "En attente"
    st.sidebar.markdown(
        f'<div style="font-size:10px;color:{color};padding:4px 0">'
        f'{dot} <span style="color:{color};font-weight:600">{status_text}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def category_badge(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#374151")
    return (
        f'<span style="display:inline-block;background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:2px;font-size:8px;font-weight:700;'
        f'letter-spacing:0.8px;text-transform:uppercase">{cat}</span>'
    )


_PAYWALLED_SOURCES = {
    "ft", "financial times", "bloomberg", "wsj", "wall street journal",
    "economist", "les echos", "la tribune", "le figaro",
}

_GNEWS_SOURCES = {
    "bloomberg (gnews)", "s&p ratings", "moody's", "fitch",
    "m&a deals", "levfin", "pe / buyouts", "dcm / bonds", "distressed",
    "energy deals", "defense", "tech / big tech", "aviation", "retail / luxe",
    "healthcare / pharma", "real estate", "macro global (gnews)", "trade / sanctions",
    "banking results", "banking regulation", "banking m&a",
    "nominations finance", "nominations banques", "esg / green finance",
    "esm/esrb (gnews)",
}


def _is_paywalled(source: str) -> bool:
    s = source.lower()
    return any(p in s for p in _PAYWALLED_SOURCES)


def _search_url(headline: str, source: str) -> str:
    import urllib.parse
    q = urllib.parse.quote_plus(f"{headline} {source}")
    return f"https://www.google.com/search?q={q}"


# Marqueurs de texte heuristique (fallback quand Gemini est indisponible)
# Ces valeurs ne sont PAS de vraies analyses — on les masque dans l'UI.
_HEURISTIC_PREFIXES = (
    "[Analyse LLM indisponible",
    "Développement sectoriel",
    "Transaction M&A",
    "Event crédit leveraged",
    "Event de crédit affectant",
    "Développement énergétique",
    "Signal macro (",
    "Risque géopolitique (",
    "Développement réglementaire",
    "Nomination dans le secteur",
    "Actualité bancaire (",
    "News ",
)


def _is_real_so_what(text: str) -> bool:
    """Return True only if text is a real Gemini analysis (not a heuristic fallback)."""
    t = (text or "").strip()
    if not t:
        return False
    return not any(t.startswith(p) for p in _HEURISTIC_PREFIXES)


def news_card(item: dict, highlight_fn=None) -> None:
    """Render a single news card with gold analysis block.
    highlight_fn(text) -> html  for search result highlighting.
    """
    def hl(text: str) -> str:
        return highlight_fn(text) if highlight_fn else (text or "")

    cat          = item.get("category", "Sector")
    color        = CATEGORY_COLORS.get(cat, "#374151")
    url          = item.get("url", "")
    raw_headline = item.get("headline", item.get("title", ""))
    headline     = hl(raw_headline)
    summary      = hl(item.get("summary", ""))
    _sw_raw      = (item.get("so_what", "") or "").strip()
    # Masquer le texte heuristique (fallback Gemini indisponible) — ne montrer que la vraie analyse
    so_what      = hl(_sw_raw) if _is_real_so_what(_sw_raw) else ""

    source     = item.get("source", "")
    is_gnews   = "news.google.com" in url or source.lower() in _GNEWS_SOURCES
    is_paywall = _is_paywalled(source)

    # ── Badges ────────────────────────────────────────────────────────────
    cat_badge = (
        f'<span style="display:inline-block;background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:2px;font-size:8px;font-weight:700;'
        f'letter-spacing:0.8px;text-transform:uppercase;margin-right:5px">{cat}</span>'
    )

    extra_badges = ""
    if item.get("deal_size_eur"):
        extra_badges += (
            f'<span style="display:inline-block;background:#EBF4FF;color:#0B2545;'
            f'padding:2px 8px;border-radius:2px;font-size:9px;font-weight:700;'
            f'margin-right:5px">{item["deal_size_eur"]/1e9:.1f}&nbsp;Md€</span>'
        )
    if item.get("source_count", 1) >= 2:
        cnt = item["source_count"]
        extra_badges += (
            f'<span style="display:inline-block;color:#059669;background:#F0FAF4;'
            f'border:1px solid #A7F3D0;padding:2px 7px;border-radius:2px;'
            f'font-size:8.5px;font-weight:600;margin-right:5px">'
            f'✓ {cnt} sources</span>'
        )
    if item.get("confidence") == "medium":
        extra_badges += (
            '<span style="display:inline-block;color:#92400E;background:#FFFBEB;'
            'border:1px solid #FDE68A;padding:2px 7px;border-radius:2px;'
            'font-size:8.5px;font-weight:600;margin-right:5px">⚠ à vérifier</span>'
        )
    if is_paywall:
        extra_badges += (
            '<span style="display:inline-block;color:#6B7280;background:#F9FAFB;'
            'border:1px solid #E5E7EB;padding:2px 7px;border-radius:2px;'
            'font-size:8.5px;font-weight:500">🔒 Abonné</span>'
        )

    # ── Meta line ─────────────────────────────────────────────────────────
    sep = '<span style="color:#D1D5DB;margin:0 5px">·</span>'
    meta_parts = [
        source,
        item.get("date", ""),
        item.get("geography", ""),
        item.get("sector", ""),
    ]
    meta = sep.join(
        f'<span style="color:#9CA3AF">{p}</span>'
        for p in meta_parts if p
    )

    search_fallback = _search_url(raw_headline, source)
    if url and not is_gnews:
        meta += (
            f'{sep}<a href="{url}" target="_blank" '
            f'style="color:#0B2545;font-weight:600;text-decoration:none;font-size:10.5px;'
            f'border-bottom:1px solid rgba(11,37,69,0.2);padding-bottom:1px">Lire &#8594;</a>'
        )
        if is_paywall:
            meta += (
                f'{sep}<a href="{search_fallback}" target="_blank" '
                f'style="color:#9CA3AF;font-size:10px;font-weight:500;text-decoration:none">Rechercher</a>'
            )
    elif url:
        meta += (
            f'{sep}<a href="{search_fallback}" target="_blank" '
            f'style="color:#0B2545;font-weight:600;text-decoration:none;font-size:10.5px;'
            f'border-bottom:1px solid rgba(11,37,69,0.2);padding-bottom:1px">Rechercher &#8594;</a>'
        )
        if item.get("publisher_domain"):
            domain = (
                item["publisher_domain"]
                .replace("https://", "").replace("http://", "").rstrip("/")
            )
            meta += f'{sep}<span style="color:#9CA3AF;font-size:10px">{domain}</span>'

    # ── Rank ──────────────────────────────────────────────────────────────
    rank = item.get("rank", "")
    rank_html = (
        f'<span style="font-family:\'Playfair Display\',Georgia,serif;'
        f'font-size:12px;font-weight:700;color:#C9A84C;margin-right:10px;'
        f'letter-spacing:0.5px">{str(rank).zfill(2)}</span>'
        if rank else ""
    )

    headline_href = search_fallback if is_gnews else (url or search_fallback)

    # ── Analysis block ────────────────────────────────────────────────────
    if so_what:
        analysis_html = (
            '<div style="background:linear-gradient(135deg,#FAFBFD 0%,#F8F9FC 100%);'
            'border-left:3px solid #C9A84C;padding:14px 18px 12px;'
            'border-radius:0 4px 4px 0;margin-top:14px;'
            'box-shadow:inset 0 0 0 1px rgba(201,168,76,0.1)">'
            '<div style="font-size:7.5px;font-weight:700;letter-spacing:2.5px;'
            'text-transform:uppercase;color:#C9A84C;margin-bottom:9px;'
            'display:flex;align-items:center;gap:6px">'
            '<span style="width:12px;height:1px;background:#C9A84C;display:inline-block"></span>'
            'Analyse d\'impact &amp; conséquences'
            '<span style="width:12px;height:1px;background:#C9A84C;display:inline-block"></span>'
            '</div>'
            f'<div style="font-size:13px;line-height:1.8;color:#1E3A5F;'
            f'font-weight:400">{so_what}</div>'
            '</div>'
        )
    else:
        analysis_html = (
            '<div style="margin-top:12px;padding:10px 14px;background:#F9FAFB;'
            'border-radius:4px;border:1px dashed #E2E8F0">'
            '<span style="font-size:11px;color:#B0BAC7;font-style:italic">'
            'Analyse non disponible pour cette édition.'
            '</span>'
            '</div>'
        )

    # ── Full card ─────────────────────────────────────────────────────────
    card = (
        f'<div style="background:#FFFFFF;border-left:4px solid {color};'
        f'padding:20px 24px 18px;margin-bottom:12px;border-radius:0 6px 6px 0;'
        f'box-shadow:0 2px 8px rgba(11,37,69,0.06),0 0 0 1px rgba(11,37,69,0.04);'
        f'transition:box-shadow 0.2s ease">'

        # Header row: rank + category badge + extras
        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:11px">'
        f'{rank_html}{cat_badge}{extra_badges}'
        f'</div>'

        # Headline (linked)
        f'<a href="{headline_href}" target="_blank" style="'
        f'font-family:\'Playfair Display\',Georgia,serif;'
        f'font-size:16.5px;font-weight:700;color:#071828;text-decoration:none;'
        f'line-height:1.38;display:block;margin-bottom:9px;'
        f'transition:color 0.15s ease" '
        f'onmouseover="this.style.color=\'#0B2545\'" '
        f'onmouseout="this.style.color=\'#071828\'">'
        f'{headline}</a>'

        # Meta line
        f'<div style="font-size:10.5px;margin-bottom:13px;line-height:1.7">{meta}</div>'

        # Summary
        f'<div style="font-size:13.5px;line-height:1.8;color:#374151;'
        f'border-left:0px solid transparent;margin-bottom:2px">{summary}</div>'

        + analysis_html
        + '</div>'
    )

    st.markdown(card, unsafe_allow_html=True)
