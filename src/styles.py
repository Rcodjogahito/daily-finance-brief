"""Shared Streamlit CSS and UI helpers — Coffee Economics News design system."""
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

# Human-readable labels for the UI (type d'information filter)
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] * {
    font-family: 'Goldman Sans', 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Sidebar dark ───────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0B1D2E !important;
    border-right: 1px solid #1A3048 !important;
}
[data-testid="stSidebar"] * { color: #8FAFC8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #E2EAF2 !important; font-weight: 600 !important; font-size: 0.85rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }
[data-testid="stSidebar"] a { color: #4A90D9 !important; text-decoration: none !important; }
[data-testid="stSidebar"] a:hover { color: #7AB8F5 !important; }
[data-testid="stSidebar"] hr { border-color: #1A3048 !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] { color: #E2EAF2 !important; font-size: 1.15rem !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color: #4A7FA5 !important; font-size: 0.65rem !important; }

/* ── Main content ───────────────────────────────── */
.main .block-container {
    padding: 2rem 2.5rem;
    max-width: 940px;
}

h1 {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #0B1D2E !important;
    letter-spacing: -0.4px !important;
    margin-bottom: 0.1rem !important;
}
h2 { font-size: 1.1rem !important; font-weight: 600 !important; color: #0B1D2E !important; }
h3 { font-size: 0.9rem !important; font-weight: 600 !important; color: #374151 !important; }

/* ── Metrics ────────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: #0B1D2E !important;
    letter-spacing: -0.3px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
}

/* ── Buttons ────────────────────────────────────── */
.stButton > button {
    background: #0B1D2E !important;
    color: white !important;
    border: none !important;
    border-radius: 2px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
}
.stButton > button:hover { background: #1A3A5C !important; }
.stDownloadButton > button {
    background: white !important;
    color: #0B1D2E !important;
    border: 1px solid #DDE1E7 !important;
    border-radius: 2px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
}

/* ── Form labels ────────────────────────────────── */
.stSelectbox label, .stMultiSelect label,
.stRadio label, .stTextInput label, .stDateInput label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #6B7A8E !important;
}

/* ── Info / warning boxes ───────────────────────── */
[data-testid="stInfo"] {
    background: #F0F6FF !important;
    border: none !important;
    border-left: 2px solid #1565C0 !important;
    border-radius: 0 3px 3px 0 !important;
    color: #1E3A5F !important;
    font-size: 0.84rem !important;
}

/* ── Expander ───────────────────────────────────── */
details summary {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
}

/* ── Divider ────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid #E9ECF0 !important; margin: 0.5rem 0 !important; }

/* ── Twemoji — taille et alignement des SVG emoji ── */
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
  /* Replace browser emoji with Twemoji SVGs (Twitter open-source set, v14).
     Uses jsDelivr CDN — no external dependency on twemoji.maxcdn.com.
     MutationObserver + rAF debounce handles Streamlit's React re-renders. */
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
<div style="padding:20px 0 12px">
  <div style="font-size:8px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#3A6480;margin-bottom:6px">Coffee Economics News</div>
  <div style="font-size:17px;font-weight:700;color:#E2EAF2;letter-spacing:-0.3px">Daily Finance Brief</div>
</div>
"""


_SIDEBAR_TOGGLE_JS = """
<script>
function toggleSidebar() {
  var btn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button');
  if (!btn) btn = window.parent.document.querySelector('[data-testid="stSidebarCollapsedControl"]');
  if (btn) btn.click();
}
</script>
<button onclick="toggleSidebar()" title="Afficher / masquer la barre latérale"
  style="background:#0B1D2E;color:#E2EAF2;border:none;border-radius:2px;
         padding:5px 11px;font-size:11px;font-weight:600;cursor:pointer;
         letter-spacing:0.04em;line-height:1">&#9776; Barre</button>
"""

_HOME_BUTTON = """
<a href="/" target="_self"
   style="display:inline-block;background:#1A3A5C;color:#E2EAF2;border:none;
          border-radius:2px;padding:5px 11px;font-size:11px;font-weight:600;
          text-decoration:none;letter-spacing:0.04em;line-height:1;margin-left:6px">
  &#8962; Accueil</a>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_TWEMOJI_SCRIPT, unsafe_allow_html=True)


def page_toolbar() -> None:
    """Render a small toolbar with sidebar toggle + home button at the top of main content."""
    st.markdown(
        f'<div style="margin-bottom:12px">{_SIDEBAR_TOGGLE_JS}{_HOME_BUTTON}</div>',
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(_SIDEBAR_BRAND, unsafe_allow_html=True)


def category_badge(cat: str) -> str:
    color = CATEGORY_COLORS.get(cat, "#374151")
    return (
        f'<span style="background:{color};color:#fff;padding:2px 6px;'
        f'border-radius:2px;font-size:9px;font-weight:700;'
        f'letter-spacing:0.7px;text-transform:uppercase">{cat}</span>'
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

    cat   = item.get("category", "Sector")
    color = CATEGORY_COLORS.get(cat, "#374151")
    url   = item.get("url", "")
    raw_headline = item.get("headline", item.get("title", ""))
    headline = hl(raw_headline)
    summary  = hl(item.get("summary", ""))
    _sw_raw  = item.get("so_what", "") or ""
    so_what  = hl(_sw_raw) if "[Analyse LLM indisponible" not in _sw_raw else ""

    source = item.get("source", "")
    is_gnews = "news.google.com" in url or source.lower() in _GNEWS_SOURCES
    is_paywall = _is_paywalled(source)

    # Tags row
    tags = (
        f'<span style="background:{color};color:#fff;padding:2px 6px;border-radius:2px;'
        f'font-size:9px;font-weight:700;letter-spacing:0.7px;text-transform:uppercase">{cat}</span>'
    )
    if item.get("deal_size_eur"):
        tags += (
            f' <span style="background:#EBF2FF;color:#0B1D2E;padding:2px 6px;'
            f'border-radius:2px;font-size:10px;font-weight:700">'
            f'{item["deal_size_eur"]/1e9:.1f} Md€</span>'
        )
    if item.get("source_count", 1) >= 2:
        tags += f' <span style="color:#059669;font-size:10px;font-weight:600">{item["source_count"]} sources</span>'
    if item.get("confidence") == "medium":
        tags += ' <span style="color:#D97706;font-size:10px;font-weight:600">&#9888; à vérifier</span>'
    if is_paywall:
        tags += ' <span style="color:#9CA3AF;font-size:10px;font-weight:500">&#128274; Accès abonné</span>'

    # Meta line — link logic
    sep = ' <span style="color:#D1D5DB">·</span> '
    meta_parts = [source, item.get("date", ""), item.get("geography", ""), item.get("sector", "")]
    meta = sep.join(p for p in meta_parts if p)

    search_fallback = _search_url(raw_headline, source)
    if url and not is_gnews:
        meta += f'{sep}<a href="{url}" target="_blank" style="color:#1565C0;font-weight:500;text-decoration:none">Lire</a>'
        if is_paywall:
            meta += f'{sep}<a href="{search_fallback}" target="_blank" style="color:#6B7A8E;font-size:10px;font-weight:500;text-decoration:none">Rechercher</a>'
    elif url:
        # Google News URL — link via search for reliability in EU
        meta += f'{sep}<a href="{search_fallback}" target="_blank" style="color:#1565C0;font-weight:500;text-decoration:none">Rechercher l\'article</a>'
        if item.get("publisher_domain"):
            domain = item["publisher_domain"].replace("https://", "").replace("http://", "").rstrip("/")
            meta += f'{sep}<span style="color:#9CA3AF;font-size:10px">{domain}</span>'

    rank = item.get("rank", "")
    rank_str = f'<span style="font-size:10px;font-weight:700;color:#9CA3AF;margin-right:6px">{str(rank).zfill(2)}</span>' if rank else ""

    # Headline link: direct article for non-GNews, search for GNews
    headline_href = search_fallback if is_gnews else (url or search_fallback)

    with st.container():
        st.markdown(
            f'<div style="padding:18px 0 6px">{rank_str}{tags}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<a href="{headline_href}" target="_blank" style="font-size:16.5px;font-weight:700;'
            f'color:#0B1D2E;text-decoration:none;line-height:1.35;display:block;'
            f'margin-bottom:6px">{headline}</a>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:11px;color:#9CA3AF;margin-bottom:10px">{meta}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:13.5px;line-height:1.7;color:#374151;margin-bottom:10px">{summary}</div>',
            unsafe_allow_html=True,
        )
        if so_what:
            st.markdown(
                f'<div style="background:#F0F6FF;border-left:3px solid #1565C0;'
                f'padding:12px 16px;border-radius:0 3px 3px 0;margin-bottom:4px">'
                f'<span style="font-size:8px;font-weight:700;letter-spacing:2px;'
                f'text-transform:uppercase;color:#1565C0;display:block;margin-bottom:7px">'
                f'Analyse d\'impact &amp; conséquences</span>'
                f'<span style="font-size:13px;line-height:1.7;color:#1E3A5F">{so_what}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#F9FAFB;border-left:3px solid #D1D5DB;'
                'padding:10px 14px;border-radius:0 3px 3px 0;margin-bottom:4px">'
                '<span style="font-size:11px;color:#9CA3AF;font-style:italic">'
                'Analyse d\'impact non disponible pour cette édition.</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div style="border-top:1px solid #E9ECF0;margin-top:14px"></div>',
            unsafe_allow_html=True,
        )
