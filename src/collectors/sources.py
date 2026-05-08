SOURCES: dict[str, str] = {
    # ── Anglo-saxonnes premium ─────────────────────────────────────────────
    "Reuters Business":    "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "Reuters Markets":     "https://www.reutersagency.com/feed/?best-topics=markets",
    "Reuters Energy":      "https://www.reutersagency.com/feed/?best-topics=energy",
    "Reuters Deals":       "https://www.reutersagency.com/feed/?best-topics=deals",
    "Reuters Tech":        "https://www.reutersagency.com/feed/?best-topics=tech",

    "FT Companies":        "https://www.ft.com/companies?format=rss",
    "FT Markets":          "https://www.ft.com/markets?format=rss",

    "WSJ Business":        "https://feeds.a.dj.com/rss/RSSWSJD.xml",
    "WSJ Markets":         "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",

    "Economist Finance":   "https://www.economist.com/finance-and-economics/rss.xml",
    "Economist Business":  "https://www.economist.com/business/rss.xml",

    "Bloomberg (GNews)":   "https://news.google.com/rss/search?q=site:bloomberg.com+when:1d&hl=en-US&gl=US&ceid=US:en",

    "CNBC Finance":        "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "MarketWatch":         "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Barron's":            "https://www.barrons.com/feed/rss/markets_real_time",

    # ── Françaises ────────────────────────────────────────────────────────
    "Le Monde Économie":   "https://www.lemonde.fr/economie/rss_full.xml",
    "Les Echos Marchés":   "https://syndication.lesechos.fr/rss/rss_finance-marches.xml",
    "Les Echos Industrie": "https://syndication.lesechos.fr/rss/rss_industrie-services.xml",
    "Les Echos Tech":      "https://syndication.lesechos.fr/rss/rss_tech-medias.xml",
    "L'AGEFI":             "https://www.agefi.fr/rss",
    "La Tribune":          "https://www.latribune.fr/rss/",
    "Le Figaro Eco":       "https://www.lefigaro.fr/rss/figaro_economie.xml",

    # ── Institutions financières internationales ───────────────────────────
    "ECB Press":           "https://www.ecb.europa.eu/rss/press.html",
    "Fed Press":           "https://www.federalreserve.gov/feeds/press_all.xml",
    "BoE":                 "https://www.bankofengland.co.uk/rss/news",
    "BIS Research":        "https://www.bis.org/doclist/bis_rss.xml",
    "IMF News":            "https://www.imf.org/en/News/rss",
    "ESM/ESRB (GNews)":    "https://news.google.com/rss/search?q=(ESM+OR+ESRB+OR+%22European+Stability+Mechanism%22)+when:2d&hl=en",

    # ── Ratings — flux directs et via Google News ─────────────────────────
    "S&P Ratings":         "https://news.google.com/rss/search?q=%22S%26P+Global%22+rating+(downgrade+OR+upgrade+OR+outlook)+when:1d&hl=en",
    "Moody's":             "https://news.google.com/rss/search?q=Moody%27s+rating+(downgrade+OR+upgrade+OR+outlook)+when:1d&hl=en",
    "Fitch":               "https://news.google.com/rss/search?q=Fitch+rating+(downgrade+OR+upgrade+OR+outlook)+when:1d&hl=en",

    # ── Deal flow M&A, LevFin, PE ─────────────────────────────────────────
    "M&A Deals":           "https://news.google.com/rss/search?q=(%22acquires%22+OR+%22merger%22+OR+%22LBO%22+OR+%22buyout%22)+(billion+OR+%22Md%22)+when:1d&hl=en",
    "LevFin":              "https://news.google.com/rss/search?q=(%22leveraged+loan%22+OR+%22high+yield%22+OR+%22refinancing%22+OR+%22covenant%22+OR+CLO)+when:1d&hl=en",
    "PE / Buyouts":        "https://news.google.com/rss/search?q=(%22buyout%22+OR+%22LBO%22+OR+%22private+equity%22+OR+%22KKR%22+OR+%22Blackstone%22+OR+%22Carlyle%22)+when:1d&hl=en",
    "DCM / Bonds":         "https://news.google.com/rss/search?q=(%22bond+issuance%22+OR+%22green+bond%22+OR+%22high+yield+bond%22+OR+%22debt+capital+markets%22)+when:1d&hl=en",
    "Distressed":          "https://news.google.com/rss/search?q=(distressed+OR+restructuring+OR+%22Chapter+11%22+OR+default+OR+%22fallen+angel%22)+when:1d&hl=en",

    # ── Deal flow — secteurs spécifiques ──────────────────────────────────
    "Energy Deals":        "https://news.google.com/rss/search?q=(oil+OR+gas+OR+renewable+OR+%22project+finance%22+OR+LNG)+(deal+OR+financing+OR+acquisition+OR+FID)+when:1d&hl=en",
    "Defense":             "https://news.google.com/rss/search?q=(defense+OR+defence+OR+%22military+contract%22+OR+aerospace+OR+OTAN+OR+NATO)+(contract+OR+deal+OR+procurement)+when:1d&hl=en",
    "Tech / Big Tech":     "https://news.google.com/rss/search?q=(Microsoft+OR+Google+OR+Apple+OR+Amazon+OR+Meta+OR+Nvidia+OR+Alphabet)+(earnings+OR+deal+OR+acquisition+OR+layoff)+when:1d&hl=en",
    "Aviation":            "https://news.google.com/rss/search?q=(Airbus+OR+Boeing+OR+%22airline%22+OR+aerospace)+(deal+OR+earnings+OR+contract+OR+order)+when:1d&hl=en",
    "Retail / Luxe":       "https://news.google.com/rss/search?q=(LVMH+OR+Kering+OR+Hermes+OR+luxury+OR+Richemont)+(earnings+OR+deal+OR+results)+when:1d&hl=en",
    "Healthcare / Pharma": "https://news.google.com/rss/search?q=(pharma+OR+biotech+OR+healthcare)+(deal+OR+acquisition+OR+merger+OR+FDA)+when:1d&hl=en",
    "Real Estate":         "https://news.google.com/rss/search?q=(%22real+estate%22+OR+REIT+OR+immobilier)+(deal+OR+acquisition+OR+earnings)+when:1d&hl=en",

    # ── Macro & banques centrales élargi ──────────────────────────────────
    "Macro Global (GNews)":"https://news.google.com/rss/search?q=(inflation+OR+CPI+OR+PMI+OR+%22interest+rate%22+OR+%22rate+cut%22+OR+%22rate+hike%22)+when:1d&hl=en",
    "Trade / Sanctions":   "https://news.google.com/rss/search?q=(sanctions+OR+tariffs+OR+%22trade+war%22+OR+reshoring+OR+%22export+control%22)+when:1d&hl=en",

    # ── Actualité bancaire ────────────────────────────────────────────────
    "Banking Results":     "https://news.google.com/rss/search?q=(bank+OR+banque)+(results+OR+earnings+OR+%22profit%22+OR+%22résultats%22)+(BNP+OR+SocGen+OR+Crédit+OR+HSBC+OR+Deutsche+OR+Barclays+OR+UBS+OR+JPMorgan)+when:1d&hl=en",
    "Banking Regulation":  "https://news.google.com/rss/search?q=(%22Basel+IV%22+OR+%22Bâle+IV%22+OR+CET1+OR+MREL+OR+%22stress+test%22+OR+%22EBA%22+OR+%22SREP%22)+when:2d&hl=en",
    "Banking M&A":         "https://news.google.com/rss/search?q=(bank+OR+banque)+(merger+OR+acquisition+OR+consolidation)+when:2d&hl=en",

    # ── Nominations importantes ───────────────────────────────────────────
    "Nominations Finance": "https://news.google.com/rss/search?q=(%22appointed+CEO%22+OR+%22appointed+CFO%22+OR+%22named+CEO%22+OR+%22new+chief+executive%22+OR+%22directeur+général+nommé%22)+finance+when:2d&hl=en",
    "Nominations Banques": "https://news.google.com/rss/search?q=(%22appointed%22+OR+%22nommé%22+OR+%22named%22)+(bank+OR+banque+OR+%22asset+manager%22+OR+%22private+equity%22)+when:2d&hl=en",

    # ── ESG / Finance durable ─────────────────────────────────────────────
    "ESG / Green Finance": "https://news.google.com/rss/search?q=(%22green+bond%22+OR+%22sustainability-linked%22+OR+ESG+OR+%22transition+bond%22+OR+CSRD)+when:1d&hl=en",

    # ── Commodities ───────────────────────────────────────────────────────
    "Reuters Commodities":       "https://www.reutersagency.com/feed/?best-topics=commodities",
    "Commodities / Métaux":      "https://news.google.com/rss/search?q=(gold+OR+silver+OR+copper+OR+nickel+OR+aluminium+OR+zinc+OR+%22iron+ore%22+OR+platinum+OR+LME)+(price+OR+market+OR+rally+OR+slump+OR+demand+OR+supply+OR+shortage)+when:1d&hl=en",
    "Commodities / Agri":        "https://news.google.com/rss/search?q=(wheat+OR+corn+OR+soybean+OR+sugar+OR+cocoa+OR+coffee+OR+%22palm+oil%22+OR+%22agricultural+commodity%22+OR+CBOT)+price+when:1d&hl=en",
    "Commodities / Énergie Prix":"https://news.google.com/rss/search?q=(WTI+OR+%22Brent+crude%22+OR+%22natural+gas+price%22+OR+%22crude+oil+price%22+OR+%22LNG+price%22+OR+%22coal+price%22)+when:1d&hl=en",
    "OPEC / Oil Market":         "https://news.google.com/rss/search?q=(OPEC+OR+%22oil+production%22+OR+%22oil+supply+cut%22+OR+%22oil+demand%22+OR+%22OPEC+decision%22)+when:1d&hl=en",
    "Commodities / Marchés":     "https://news.google.com/rss/search?q=(commodity+OR+commodities)+(market+OR+futures+OR+%22supply+chain%22+OR+%22commodity+index%22+OR+CFTC+OR+CME)+when:1d&hl=en",
}
