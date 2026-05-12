"""Shared Streamlit CSS and UI helpers — Daily Finance Brief design system."""
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

html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] * {
    font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0B2545 !important;
    border-right: 1px solid #132E58 !important;
}
[data-testid="stSidebar"] * { color: #8FAFC8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #E2EAF2 !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] a { color: #7FAACC !important; text-decoration: none !important; }
[data-testid="stSidebar"] a:hover { color: #C9A84C !important; }
[data-testid="stSidebar"] hr { border-color: #1A3A5C !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #F0F6FF !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    color: #4A7FA5 !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Main background ─────────────────────────────── */
[data-testid="stAppViewContainer"] > .main {
    background-color: #F7F9FC !important;
}

/* ── Main content ───────────────────────────────── */
.main .block-container {
    padding: 2.5rem 3rem;
    max-width: 1000px;
}

/* ── Typography ─────────────────────────────────── */
h1 {
    font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #0B2545 !important;
    letter-spacing: -0.5px !important;
    line-height: 1.2 !important;
    margin-bottom: 0.15rem !important;
}
h2 {
    font-family: 'Playfair Display', Georgia, 'Times New Roman', serif !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    color: #0B2545 !important;
    letter-spacing: -0.3px !important;
}
h3 {
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    color: #374151 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Metrics ────────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #0B2545 !important;
    letter-spacing: -0.5px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
}

/* ── Buttons ────────────────────────────────────── */
.stButton > button {
    background: #0B2545 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 2px !important;
    font-weight: 600 !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1.25rem !important;
}
.stButton > button:hover { background: #1A3A5C !important; }
.stDownloadButton > button {
    background: transparent !important;
    color: #0B2545 !important;
    border: 1.5px solid #0B2545 !important;
    border-radius: 2px !important;
    font-weight: 600 !important;
    font-size: 0.74rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
.stDownloadButton > button:hover {
    background: #0B2545 !important;
    color: #FFFFFF !important;
}

/* ── Form controls ──────────────────────────────── */
.stSelectbox label, .stMultiSelect label,
.stRadio label, .stTextInput label, .stDateInput label {
    font-size: 0.67rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
}

/* ── Info boxes ─────────────────────────────────── */
[data-testid="stInfo"] {
    background: #EFF6FF !important;
    border: none !important;
    border-left: 3px solid #0B2545 !important;
    border-radius: 0 3px 3px 0 !important;
    color: #0B2545 !important;
    font-size: 0.84rem !important;
}

/* ── Expander ───────────────────────────────────── */
details summary {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Divider ────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 0.75rem 0 !important;
}

/* ── Twemoji ────────────────────────────────────── */
img.emoji {
    height: 1.15em;
    width: 1.15em;
    margin: 0 0.04em 0 0.04em;
    vertical-align: -0.2em;
    display: inline;
    pointer-events: none;
}
</style>
"""

_TWEMOJI_SCRIPT = """
<script>
(function () {
  var _tw_pending = false;

  function applyTwemoji() {
    if (typeof twemoji === "undefined" || _tw_pending) return;
    _tw_pending = true;
    requestAnimationFrame(function () {
      twemoji.parse(document.body, {
        folder: "svg",
        ext: ".svg",
        base: "https://cdn.jsdelivr.net/gh/twitter/twemoji@v14.0.0/assets/"
      });
      _tw_pending = false;
    });
  }

  var s = document.createElement("script");
  s.src = "https://cdn.jsdelivr.net/npm/twemoji@14.0.2/dist/twemoji.min.js";
  s.crossOrigin = "anonymous";
  s.onload = function () {
    applyTwemoji();
    new MutationObserver(applyTwemoji).observe(
      document.body,
      { childList: true, subtree: true }
    );
  };
  document.head.appendChild(s);
})();
</script>
"""

_SIDEBAR_BRAND = """
<div style="padding:24px 0 18px;border-bottom:1px solid rgba(255,255,255,0.07);margin-bottom:4px">
  <div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:10px">Coffee Economics News</div>
  <div style="font-family:'Playfair Display',Georgia,serif;font-size:20px;font-weight:800;color:#F0F6FF;letter-spacing:-0.5px;line-height:1.25">Daily Finance<br>Brief</div>
</div>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_TWEMOJI_SCRIPT, unsafe_allow_html=True)


_TOOLBAR_HTML = """<!DOCTYPE html>
<html>
<head>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  background: transparent;
  overflow: hidden;
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
}
.bar { display: flex; gap: 6px; align-items: center; padding: 4px 0 10px 0; }
button {
  background: #0B2545; color: #E2EAF2; border: none; border-radius: 2px;
  padding: 6px 13px; font-size: 10.5px; font-weight: 600; cursor: pointer;
  letter-spacing: 0.06em; text-transform: uppercase;
}
button:hover { background: #1A3A5C; }
a {
  display: inline-block; background: transparent; color: #6B7A8E;
  border: 1px solid #D1D5DB; border-radius: 2px;
  padding: 5px 13px; font-size: 10.5px; font-weight: 600;
  text-decoration: none; letter-spacing: 0.06em; text-transform: uppercase;
}
a:hover { border-color: #0B2545; color: #0B2545; }
</style>
</head>
<body>
<div class="bar">
  <button onclick="toggleSidebar()">&#9776; Menu</button>
  <a href="/" target="_parent">&#8962; Accueil</a>
</div>
<script>
function toggleSidebar() {
  try {
    var d = window.parent.document;
    var sel = [
      'button[data-testid="stSidebarCollapseButton"]',
      '[data-testid="stSidebarCollapseButton"] button',
      '[data-testid="stSidebarCollapsedControl"] button',
      '[data-testid="stSidebarCollapsedControl"]',
    ];
    for (var i = 0; i < sel.length; i++) {
      var el = d.querySelector(sel[i]);
      if (el) { el.click(); return; }
    }
  } catch (e) {}
}
</script>
</body>
</html>"""


def page_toolbar() -> None:
    """Sidebar toggle + home button rendered in a real iframe component."""
    import streamlit.components.v1 as components
    components.html(_TOOLBAR_HTML, height=40, scrolling=False)


def sidebar_brand() -> None:
    st.sidebar.markdown(_SIDEBAR_BRAND, unsafe_allow_html=True)


def category_badge(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#374151")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 7px;'
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


def news_card(item: dict, highlight_fn=None) -> None:
    """Render a single news card. highlight_fn(text) -> html for search highlighting."""
    def hl(text: str) -> str:
        return highlight_fn(text) if highlight_fn else (text or "")

    cat          = item.get("category", "Sector")
    color        = CATEGORY_COLORS.get(cat, "#374151")
    url          = item.get("url", "")
    raw_headline = item.get("headline", item.get("title", ""))
    headline     = hl(raw_headline)
    summary      = hl(item.get("summary", ""))
    _sw_raw      = item.get("so_what", "") or ""
    so_what      = hl(_sw_raw) if "[Analyse LLM indisponible" not in _sw_raw else ""

    source    = item.get("source", "")
    is_gnews  = "news.google.com" in url or source.lower() in _GNEWS_SOURCES
    is_paywall = _is_paywalled(source)

    # Category badge
    badge = (
        f'<span style="display:inline-block;background:{color};color:#fff;'
        f'padding:2px 7px;border-radius:2px;font-size:8px;font-weight:700;'
        f'letter-spacing:0.8px;text-transform:uppercase;margin-right:4px">{cat}</span>'
    )

    # Extra badges
    extras = ""
    if item.get("deal_size_eur"):
        extras += (
            f'<span style="display:inline-block;background:#EBF4FF;color:#0B2545;'
            f'padding:2px 7px;border-radius:2px;font-size:9px;font-weight:700;'
            f'margin-right:4px">{item["deal_size_eur"]/1e9:.1f}&nbsp;Md€</span>'
        )
    if item.get("source_count", 1) >= 2:
        extras += (
            f'<span style="color:#059669;font-size:9px;font-weight:600;'
            f'margin-right:4px">{item["source_count"]} sources</span>'
        )
    if item.get("confidence") == "medium":
        extras += (
            '<span style="color:#D97706;font-size:9px;font-weight:600;'
            'margin-right:4px">&#9888; à vérifier</span>'
        )
    if is_paywall:
        extras += (
            '<span style="color:#9CA3AF;font-size:9px;font-weight:500">'
            '&#128274; Abonné</span>'
        )

    # Meta line
    sep = '<span style="color:#D1D5DB;margin:0 4px">·</span>'
    meta_parts = [
        source,
        item.get("date", ""),
        item.get("geography", ""),
        item.get("sector", ""),
    ]
    meta = sep.join(
        f'<span style="color:#9CA3AF">{p}</span>' for p in meta_parts if p
    )

    search_fallback = _search_url(raw_headline, source)
    if url and not is_gnews:
        meta += (
            f'{sep}<a href="{url}" target="_blank" '
            f'style="color:#0B2545;font-weight:600;text-decoration:none;'
            f'font-size:10.5px">Lire &#8594;</a>'
        )
        if is_paywall:
            meta += (
                f'{sep}<a href="{search_fallback}" target="_blank" '
                f'style="color:#9CA3AF;font-size:10px;font-weight:500;'
                f'text-decoration:none">Rechercher</a>'
            )
    elif url:
        meta += (
            f'{sep}<a href="{search_fallback}" target="_blank" '
            f'style="color:#0B2545;font-weight:600;text-decoration:none;'
            f'font-size:10.5px">Rechercher &#8594;</a>'
        )
        if item.get("publisher_domain"):
            domain = (
                item["publisher_domain"]
                .replace("https://", "").replace("http://", "").rstrip("/")
            )
            meta += f'{sep}<span style="color:#9CA3AF;font-size:10px">{domain}</span>'

    # Rank number
    rank = item.get("rank", "")
    rank_html = (
        f'<span style="font-size:11px;font-weight:700;color:#C9A84C;'
        f'margin-right:8px">{str(rank).zfill(2)}</span>'
        if rank else ""
    )

    headline_href = search_fallback if is_gnews else (url or search_fallback)

    # Analysis / so-what block
    if so_what:
        analysis_html = (
            '<div style="background:#FAFBFD;border-left:3px solid #C9A84C;'
            'padding:14px 18px;border-radius:0 3px 3px 0;margin-top:14px">'
            '<div style="font-size:8px;font-weight:700;letter-spacing:2.5px;'
            'text-transform:uppercase;color:#C9A84C;margin-bottom:8px">'
            "Analyse d'impact &amp; conséquences</div>"
            f'<div style="font-size:13px;line-height:1.75;color:#1E3A5F">{so_what}</div>'
            '</div>'
        )
    else:
        analysis_html = (
            '<div style="margin-top:10px">'
            '<span style="font-size:11px;color:#C8D0DC;font-style:italic">'
            "Analyse non disponible pour cette édition.</span>"
            '</div>'
        )

    card = (
        f'<div style="background:#FFFFFF;border-left:3px solid {color};'
        f'padding:20px 24px 18px;margin-bottom:10px;border-radius:0 4px 4px 0;'
        f'box-shadow:0 1px 4px rgba(11,37,69,0.07),0 0 0 1px rgba(11,37,69,0.04)">'
        f'<div style="margin-bottom:10px">{rank_html}{badge}{extras}</div>'
        f'<a href="{headline_href}" target="_blank" style="'
        "font-family:'Playfair Display',Georgia,serif;"
        f'font-size:16px;font-weight:700;color:#0B2545;text-decoration:none;'
        f'line-height:1.38;display:block;margin-bottom:8px">{headline}</a>'
        f'<div style="font-size:10.5px;margin-bottom:12px;line-height:1.6">'
        f'{meta}</div>'
        f'<div style="font-size:13.5px;line-height:1.75;color:#374151;'
        f'margin-bottom:4px">{summary}</div>'
        + analysis_html
        + '</div>'
    )

    st.markdown(card, unsafe_allow_html=True)
