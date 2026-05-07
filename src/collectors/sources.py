SOURCES: dict[str, str] = {
    # Anglo-saxonnes premium
    "Reuters Business":    "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "Reuters Markets":     "https://www.reutersagency.com/feed/?best-topics=markets",
    "Reuters Energy":      "https://www.reutersagency.com/feed/?best-topics=energy",
    "Reuters Deals":       "https://www.reutersagency.com/feed/?best-topics=deals",
    "Reuters Tech":        "https://www.reutersagency.com/feed/?best-topics=tech",
    "FT Companies":        "https://www.ft.com/companies?format=rss",
    "FT Markets":          "https://www.ft.com/markets?format=rss",
    "FT Lex":              "https://www.ft.com/lex?format=rss",
    "Bloomberg (GNews)":   "https://news.google.com/rss/search?q=site:bloomberg.com+when:1d&hl=en-US&gl=US&ceid=US:en",
    "WSJ Business":        "https://feeds.a.dj.com/rss/RSSWSJD.xml",
    "Economist Finance":   "https://www.economist.com/finance-and-economics/rss.xml",
    "Economist Business":  "https://www.economist.com/business/rss.xml",

    # Françaises
    "Le Monde Économie":   "https://www.lemonde.fr/economie/rss_full.xml",
    "Les Echos Marchés":   "https://syndication.lesechos.fr/rss/rss_finance-marches.xml",
    "Les Echos Industrie": "https://syndication.lesechos.fr/rss/rss_industrie-services.xml",
    "Les Echos Tech":      "https://syndication.lesechos.fr/rss/rss_tech-medias.xml",
    "L'AGEFI":             "https://www.agefi.fr/rss",

    # Banques centrales / régulateurs
    "ECB Press":           "https://www.ecb.europa.eu/rss/press.html",
    "Fed Press":           "https://www.federalreserve.gov/feeds/press_all.xml",
    "BoE":                 "https://www.bankofengland.co.uk/rss/news",

    # Ratings (Google News)
    "S&P Ratings":         "https://news.google.com/rss/search?q=%22S%26P+Global%22+rating+(downgrade+OR+upgrade)+when:1d&hl=en",
    "Moody's":             "https://news.google.com/rss/search?q=Moody%27s+rating+(downgrade+OR+upgrade)+when:1d&hl=en",
    "Fitch":               "https://news.google.com/rss/search?q=Fitch+rating+(downgrade+OR+upgrade)+when:1d&hl=en",

    # Deal flow ciblé via Google News
    "M&A Deals":           "https://news.google.com/rss/search?q=(%22acquires%22+OR+%22merger%22+OR+%22LBO%22)+(billion+OR+%22%E2%82%AC%22)+when:1d&hl=en",
    "LevFin":              "https://news.google.com/rss/search?q=(%22leveraged+loan%22+OR+%22high+yield%22+OR+%22refinancing%22+OR+%22covenant%22)+when:1d&hl=en",
    "Energy Deals":        "https://news.google.com/rss/search?q=(oil+OR+gas+OR+renewable+OR+%22project+finance%22)+(deal+OR+financing+OR+acquisition)+when:1d&hl=en",
    "PE / Buyouts":        "https://news.google.com/rss/search?q=(%22buyout%22+OR+%22LBO%22+OR+%22sponsor%22)+when:1d&hl=en",
    "Restructuring":       "https://news.google.com/rss/search?q=(distressed+OR+restructuring+OR+%22Chapter+11%22+OR+default)+when:1d&hl=en",

    # Sectoriels élargis
    "Defense":             "https://news.google.com/rss/search?q=(defense+OR+defence+OR+%22military+contract%22+OR+aerospace+procurement)+when:1d&hl=en",
    "Tech / Big Tech":     "https://news.google.com/rss/search?q=(Microsoft+OR+Google+OR+Apple+OR+Amazon+OR+Meta+OR+Nvidia)+(earnings+OR+deal+OR+acquisition)+when:1d&hl=en",
    "Aviation":            "https://news.google.com/rss/search?q=(Airbus+OR+Boeing+OR+%22airline%22+OR+aerospace)+(deal+OR+earnings+OR+contract)+when:1d&hl=en",
    "Retail / Luxe":       "https://news.google.com/rss/search?q=(LVMH+OR+Kering+OR+Hermes+OR+luxury+OR+retail)+(earnings+OR+deal+OR+results)+when:1d&hl=en",
    "Entertainment":       "https://news.google.com/rss/search?q=(Disney+OR+Netflix+OR+Warner+OR+streaming+OR+entertainment)+(deal+OR+earnings)+when:1d&hl=en",
    "Healthcare":          "https://news.google.com/rss/search?q=(pharma+OR+biotech+OR+healthcare)+(deal+OR+acquisition+OR+merger)+when:1d&hl=en",
    "Real Estate":         "https://news.google.com/rss/search?q=(%22real+estate%22+OR+REIT+OR+immobilier)+(deal+OR+acquisition+OR+earnings)+when:1d&hl=en",
}
