"""Market snapshot — fetches key indicators at brief generation time (free, no API key)."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# yfinance tickers → display label + format
_TICKERS: dict[str, dict] = {
    "^FCHI":    {"label": "CAC 40",      "format": "index",    "unit": ""},
    "^GSPC":    {"label": "S&P 500",     "format": "index",    "unit": ""},
    "EURUSD=X": {"label": "EUR/USD",     "format": "fx",       "unit": ""},
    "BZ=F":     {"label": "Brent",       "format": "commodity","unit": "$/bl"},
    "^TNX":     {"label": "UST 10Y",     "format": "rate",     "unit": "%"},
}

_OAT_ECB_URL = (
    "https://data-api.ecb.europa.eu/service/data/FM/D.FR.EUR.FR2.BB.3L.YLD"
    "?lastNObservations=3&format=jsondata"
)


def _fetch_yf_price(ticker: str) -> Optional[float]:
    """Fetch last close price from Yahoo Finance."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        hist = t.fast_info
        price = hist.get("last_price") or hist.get("regularMarketPrice")
        if price is not None:
            return float(price)
        # Fallback: download 2d history
        df = t.history(period="2d")
        if not df.empty:
            return float(df["Close"].iloc[-1])
        return None
    except Exception as exc:
        logger.debug("yfinance fetch failed for %s: %s", ticker, exc)
        return None


def _fetch_oat_10y() -> Optional[float]:
    """Fetch French OAT 10Y yield from ECB free SDMX API."""
    try:
        import requests
        resp = requests.get(_OAT_ECB_URL, timeout=8, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        series = data["dataSets"][0]["series"]
        # Extract last observation value
        obs = list(series.values())[0]["observations"]
        last_val = list(obs.values())[-1][0]
        return float(last_val) if last_val is not None else None
    except Exception as exc:
        logger.debug("OAT 10Y fetch failed: %s", exc)
        return None


def _fmt_change(current: float, prev: float) -> str:
    """Format percentage change with sign."""
    if prev and prev != 0:
        pct = (current - prev) / abs(prev) * 100
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.2f}%"
    return ""


def _fmt_value(value: float, fmt: str) -> str:
    if fmt == "fx":
        return f"{value:.4f}"
    if fmt == "rate":
        return f"{value:.2f}%"
    if fmt == "commodity":
        return f"{value:.1f}"
    return f"{value:,.0f}"


def fetch_market_snapshot() -> dict:
    """Fetch all market indicators. Returns dict with label, value, change."""
    snapshot: dict[str, dict] = {}

    for ticker, meta in _TICKERS.items():
        label = meta["label"]
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            df = t.history(period="5d")
            if df.empty or len(df) < 2:
                raise ValueError("No data")
            current = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            change = _fmt_change(current, prev)
            value_str = _fmt_value(current, meta["format"])
            unit = meta["unit"]
            trend = "up" if current >= prev else "down"
            snapshot[label] = {
                "value": value_str,
                "unit": unit,
                "change": change,
                "trend": trend,
                "raw": current,
            }
        except Exception as exc:
            logger.warning("Market data unavailable for %s: %s", label, exc)
            snapshot[label] = {"value": "—", "unit": "", "change": "", "trend": "flat", "raw": None}

    # OAT 10Y from ECB
    oat = _fetch_oat_10y()
    snapshot["OAT 10Y"] = {
        "value": f"{oat:.2f}%" if oat else "—",
        "unit": "",
        "change": "",
        "trend": "flat",
        "raw": oat,
    }

    logger.info("Market snapshot fetched: %d indicators", sum(1 for v in snapshot.values() if v["raw"] is not None))
    return snapshot
