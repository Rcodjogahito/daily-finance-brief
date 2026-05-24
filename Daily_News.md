# Daily Finance Brief — Documentation complète
> Dernière mise à jour : 2026-05-08 | État : production, déployé sur Streamlit Cloud

---

## 1. MISSION

Système de veille financière automatisée à coût 0€ additionnel :

1. **Brief quotidien 7j/7 à 08h30 Paris** — email depuis `codjogahito@gmail.com` vers `codjo.gahito@outlook.com` + `codjo.gahito@natixis.com` avec les 10 news les plus pertinentes pour un banker CIB
2. **Alertes chaudes intraday** (lun-ven 09h-19h Paris) — MEGA_DEAL >5Md€, Fallen Angel, Profit Warning ≥20%
3. **Dashboard Streamlit public** — historique, heatmap deals, recherche full-text, abonnement email, export PDF

**Contexte utilisateur** : Analyste CIB Natixis, spécialisé Leveraged Finance / M&A / Énergie / Commodities — brief niveau senior banker, dense, factuel, actionnable.

---

## 2. ACCÈS ET IDENTIFIANTS

| Ressource | Valeur |
|---|---|
| Repo GitHub | `https://github.com/Rcodjogahito/daily-finance-brief` (PUBLIC) |
| Branche | `master` |
| Dashboard Streamlit | `https://daily-finance-brief-cib.streamlit.app` |
| Expéditeur email | `codjogahito@gmail.com` |
| Destinataires | `codjo.gahito@outlook.com`, `codjo.gahito@natixis.com` |
| Gmail App Password | `jqmgfmqtzqouflwk` (stocké dans `.env` local et GitHub Secrets) |
| Gemini API Key | `AIzaSyDsU4kxUWhfrXWNpgtGWxPsOInopeaBGnM` (stocké dans `.env` local et GitHub Secrets) |

**GitHub Secrets configurés** : `GEMINI_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `RECIPIENTS`, `STREAMLIT_URL`

**Streamlit Secrets** : configurés manuellement dans le dashboard Streamlit Cloud (même variables que `.env`)

---

## 3. ARCHITECTURE STACK

- **Python 3.11** (GitHub Actions) / 3.14 local (via uv)
- **LLM** : Google Gemini API — package `google-genai` (nouveau SDK unifié, v1.75+) — modèle `gemini-2.5-flash`
- **Email** : `smtplib` natif Python + Gmail SMTP port 465 SSL
- **Cron** : GitHub Actions free tier (2000 min/mois — ~880 min utilisées)
- **Dashboard** : Streamlit Community Cloud (free tier, repo PUBLIC obligatoire)
- **Données** : JSON dans `data/briefs/` et `data/alerts/` committés par le bot

---

## 4. STRUCTURE DU PROJET

```
D:\CLAUDE\daily-finance-brief\
├── .github/workflows/
│   ├── daily-brief.yml          # Cron 08h30 Paris, 7j/7
│   ├── hourly-alerts.yml        # Cron toutes les heures lun-ven 09h-19h
│   └── monthly-rss-health.yml   # Vérification santé sources RSS (mensuel)
├── src/
│   ├── __init__.py
│   ├── main_brief.py            # Pipeline quotidien complet
│   ├── main_alerts.py           # Pipeline horaire alertes
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── rss_collector.py     # Collecte parallèle RSS + résolution URLs GNews
│   │   └── sources.py           # 57 sources RSS configurées (voir §6)
│   ├── analyzer.py              # Gemini API (google-genai) + fallback heuristique
│   ├── alert_detector.py        # Heuristiques alertes (MEGA_DEAL, FALLEN_ANGEL, PROFIT_WARNING)
│   ├── filters.py               # Whitelist/blacklist + déduplication SequenceMatcher
│   ├── verifier.py              # Validation URL, date, anti-spam
│   ├── enrichment.py            # Détection secteur, géographie, deal_size_eur
│   ├── market_snapshot.py       # Snapshot marchés temps réel via yfinance
│   ├── emailer.py               # Gmail SMTP + fusion destinataires env + abonnés
│   ├── archiver.py              # R/W JSON + git commit/push
│   ├── subscribers.py           # Gestion abonnements (data/subscribers.json)
│   ├── styles.py                # CSS, composants Streamlit (news_card, page_toolbar, etc.)
│   └── templates/
│       ├── email_brief.html     # Template Jinja2 email quotidien
│       └── email_alert.html     # Template Jinja2 email alerte chaude
├── streamlit_app.py             # Page principale (brief du jour)
├── pages/
│   ├── 1_📅_Historique.py       # Calendar picker + filtres + export PDF
│   ├── 2_🔥_Alertes.py         # Timeline alertes + stats + chart
│   ├── 3_🌍_Heatmap.py         # Heatmap secteur×géographie (Plotly)
│   ├── 4_🔍_Recherche.py       # Full-text search + filtres avancés + export CSV
│   └── 5_📧_Abonnement.py      # Gestion abonnements email (inscription/désinscription)
├── data/
│   ├── briefs/                  # JSON archivés (ex: 2026-05-08.json)
│   ├── alerts/                  # JSON alertes (ex: 2026-05-07.json)
│   └── subscribers.json         # Liste abonnés email supplémentaires
├── tests/
│   ├── test_smoke.py
│   ├── test_render.py
│   ├── test_archiver.py
│   ├── test_alert_detector.py
│   ├── test_enrichment.py
│   └── test_verifier.py
├── scripts/
│   ├── preview_email.py         # Génère brief.html + alert.html en local
│   └── check_rss_health.py      # Teste chaque source RSS
├── .env                         # Secrets locaux (gitignorés — NE JAMAIS COMMITTER)
├── .streamlit/
│   └── secrets.toml             # Secrets Streamlit local (gitignorés)
├── requirements.txt             # Dépendances Python prod
├── packages.txt                 # Paquets apt Streamlit Cloud (vide — aucun requis)
├── .gitignore
└── README.md
```

---

## 5. PIPELINE QUOTIDIEN (main_brief.py)

```
08h30 Paris — GitHub Actions déclenche daily-brief.yml
│
├── 0. Market snapshot (yfinance — CAC 40, S&P 500, EUR/USD, etc.)
├── 1. Collecte RSS parallèle (10 workers, timeout 15s, lookback 24h)
│      → ~1000+ items bruts depuis 57 sources
├── 2. Vérification (URL alive optionnel, date fenêtre 72h, anti-spam)
├── 3. Filtrage whitelist/blacklist
├── 4. Déduplication (SequenceMatcher ratio >0.85, merge multi-sources)
├── 5. Enrichissement (secteur, géographie, deal_size_eur)
├── 6. Cap 80 candidats → envoi à Gemini 2.5 Flash
├── 7. Post-vérification anti-hallucination (montants vérifiés vs. source)
├── 7b. Résolution URLs Google News (redirect HTTP — partiel en EU)
├── 8. Sauvegarde data/briefs/YYYY-MM-DD.json
├── 9. Rendu email HTML (Jinja2)
├── 10. Envoi Gmail SMTP (expéditeur + abonnés data/subscribers.json)
└── 11. git add data/ && git commit && git push → Streamlit redéploie auto
```

**Fallback si Gemini indisponible** : `_fallback_selection()` — top N par priorité source, max 2 items/source pour la diversité, `so_what` généré par heuristique par catégorie.

---

## 6. SOURCES RSS (57 sources)

### Anglo-saxonnes premium
| Source | URL |
|---|---|
| Reuters Business/Markets/Energy/Deals/Tech | `https://www.reutersagency.com/feed/?best-topics=...` |
| FT Companies/Markets | `https://www.ft.com/...?format=rss` |
| WSJ Business/Markets | `https://feeds.a.dj.com/rss/...` |
| Economist Finance/Business | `https://www.economist.com/.../rss.xml` |
| Bloomberg (GNews) | `https://news.google.com/rss/search?q=site:bloomberg.com+when:1d...` |
| CNBC Finance | `https://www.cnbc.com/id/10000664/device/rss/rss.html` |
| MarketWatch / Barron's | Flux RSS directs |

### Françaises
Les Echos (3 flux), Le Monde Économie, L'AGEFI, La Tribune, Le Figaro Eco

### Banques centrales et institutions
ECB, Fed, BoE, BIS, IMF, ESM/ESRB

### Ratings (via GNews)
S&P Global, Moody's, Fitch — queries ciblées downgrade/upgrade/outlook

### Deal flow (GNews)
M&A Deals, LevFin, PE/Buyouts, DCM/Bonds, Distressed

### Sectoriels (GNews)
Energy Deals, Defense, Tech/Big Tech, Aviation, Retail/Luxe, Healthcare/Pharma, Real Estate

### Macro et régulation (GNews)
Macro Global, Trade/Sanctions

### Actualité bancaire (GNews)
Banking Results, Banking Regulation, Banking M&A

### Nominations (GNews)
Nominations Finance, Nominations Banques

### ESG / Finance durable (GNews)
Green Finance, Sustainability-Linked

### Commodities (GNews) — ajouté 2026-05-08
| Source | Couverture |
|---|---|
| Reuters Commodities | Flux direct Reuters |
| Commodities / Métaux | Or, argent, cuivre, nickel, aluminium, zinc, LME |
| Commodities / Agri | Blé, maïs, soja, sucre, cacao, café, huile de palme |
| Commodities / Énergie Prix | WTI, Brent, gaz naturel, LNG, charbon |
| OPEC / Oil Market | Décisions OPEC, production, demande pétrolière |
| Commodities / Marchés | CFTC, CME, futures, indices commodités |

---

## 7. ENRICHISSEMENT AUTOMATIQUE (enrichment.py)

### Secteurs détectés
`Energy`, `Commodities`, `Financials`, `Healthcare`, `TMT`, `Industrials`, `Aviation`, `Defense`, `Consumer`, `Luxury`, `Entertainment`, `Real Estate`, `Materials`, `Services`, `Other`

**Commodities** (ajouté 2026-05-08) : détecté sur keywords — `gold price`, `brent crude`, `wti`, `opec`, `wheat price`, `lme `, `cme group`, `commodity futures`, etc.

### Géographies détectées
`France`, `UK`, `Germany`, `Italy`, `Spain`, `Nordics`, `Benelux`, `Other Europe`, `USA`, `Canada`, `MENA`, `Africa`, `Asia`, `LatAm`, `Global`

### Régions (pour filtres UI)
`Europe`, `EMEA`, `APAC`, `Afrique`, `Amériques`, `Global`

### Montants deal
Regex multi-devises (€/$/£/CHF) avec multiplicateurs (billion/Md/million/trillion), conversion en EUR.

---

## 8. FILTRES (filters.py)

### Whitelist (>80 mots-clés)
M&A/deals, LevFin/DCM, Crédit/Ratings, Énergie, Macro, Nominations, Banking, Sectoriel, Géopolitique, **Commodities** (opec, wti, brent crude, gold price, copper price, lme, cme group, cftc, wheat price, cocoa price, etc.)

### Blacklist
Sport, célébrités, météo, horoscope, recettes, gossip, prix cinéma/musique, résultats sportifs

### Déduplication
`difflib.SequenceMatcher.ratio() > 0.85` — merge en cluster, winner = source prioritaire (Reuters/FT/Bloomberg=10, WSJ=9, Economist=8, Les Echos/Le Monde/AGEFI=7). Items dupliqués → `source_count > 1`, `confidence = "high"`.

---

## 9. GEMINI API (analyzer.py)

### SDK utilisé
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.2,
        max_output_tokens=16000,      # Augmenté pour éviter troncature JSON
        response_mime_type="application/json",
    ),
)
```

### Critères de sélection (prompt LLM — ordre de priorité)
1. Deal flow structurant (M&A >500M€, LBO, IPO, mandats exclusifs)
2. Leveraged Finance / DCM (refis HY, TLB, distressed, CLO)
3. Énergie (O&G, project finance, renewables)
4. **Commodities** (OPEC, prix pétrole/gaz/métaux, marchés agricoles, LME, CFTC)
5. Crédit & ratings (downgrades/upgrades, profit warnings, fallen angels)
6. Macro & banques centrales (BCE/Fed/BoE, inflation, CPI, FX)
7. Géopolitique à impact financier (sanctions, tariffs, conflits)
8. Nominations importantes (CEOs/CFOs grands corporates et institutions financières)
9. Actualité bancaire (résultats, consolidation, régulation prudentielle, CET1, MREL)
10. Sectoriel structurant (défense, tech, aviation, luxe, pharma, real estate)
11. Régulation financière (Bâle IV, CSRD, taxonomie)

### Format JSON retourné par Gemini
```json
{
  "news": [
    {
      "rank": 1,
      "category": "M&A",
      "headline": "Titre concis en français, 12 mots max",
      "source": "Reuters",
      "date": "2026-05-08",
      "url": "https://...",
      "sector": "Energy",
      "geography": "France",
      "deal_size_eur": 6500000000,
      "confidence": "high",
      "summary": "2-3 phrases factuelles : qui, quoi, combien, quand.",
      "so_what": "Analyse structurée en 3 points : (1) Impact immédiat. (2) Conséquences acteurs. (3) Signal deal flow CIB."
    }
  ]
}
```

**Catégories disponibles** : `M&A`, `LevFin`, `Energy`, `Credit`, `Macro`, `Geo`, `Reg`, `Sector`, `Nominations`, `Banking`

### Post-vérification anti-hallucination
Pour chaque news retournée par Gemini :
- URL doit exister dans le pool candidats original (sinon rejet)
- Si `deal_size_eur` présent mais absent du texte source → supprimé, `confidence = "medium"`

### Fallback (_fallback_selection)
Quand Gemini est indisponible : top N candidats par score source + source_count, cap 2 items/source, `so_what` généré par heuristique catégorie (templates par catégorie M&A/LevFin/Energy/Macro/etc.).

---

## 10. ALERTES CHAUDES (alert_detector.py)

Heuristiques pures — pas d'appel LLM pour la détection (fiabilité + économie quota).

| Type | Critère |
|---|---|
| `MEGA_DEAL` | `deal_size_eur ≥ 5Md€` + mots-clés deal (acquires, merger, buyout, lbo…) |
| `FALLEN_ANGEL` | Regex downgrade IG→HY (cut to junk, loses investment grade, fallen angel…) |
| `PROFIT_WARNING` | Regex profit warning/guidance cut avec % ≥ 20 |

**So what des alertes** : généré par Gemini via `generate_alert_so_what()` (1 req par alerte nouvelle).

---

## 11. DASHBOARD STREAMLIT

### URL
`https://daily-finance-brief-cib.streamlit.app`

### Design system (styles.py)
- Police : Goldman Sans / Inter / Helvetica Neue
- Sidebar foncée : `#0B1D2E`
- Couleurs catégories : M&A `#1A5F8C`, LevFin `#9C6000`, Energy `#5B21B6`, Credit `#1E40AF`, Macro `#374151`, Geo `#8B1A2E`, Reg `#78350F`, Sector `#0C6E85`, Nominations `#4B5563`, Banking `#0C3B6E`

### Composants partagés (src/styles.py)
- `inject_css()` — CSS global
- `sidebar_brand()` — logo "Coffee Economics News" dans sidebar
- `page_toolbar()` — barre avec bouton sidebar toggle (JS) + bouton Home
- `news_card(item, highlight_fn)` — carte news avec badges, lien, summary, so_what

### Gestion des liens articles
- **Sources paywallées** (FT, Bloomberg, WSJ, Les Echos…) → lien direct + bouton "Rechercher" (Google Search fallback)
- **GNews proxy URLs** → lien vers Google Search (les URLs proxy ne fonctionnent pas en EU à cause du consentement GDPR)
- Badge cadenas "Accès abonné" pour les sources paywallées

### Pages

**streamlit_app.py — Brief du jour**
- Snapshot marchés (CAC 40, S&P 500, EUR/USD, Oil, Gold, EUR/GBP)
- Timestamp de génération (compact, discret)
- Filtres : Région / Type d'information / Secteur
- Cartes news avec analyse d'impact
- Export Bloomberg CSV + Export PDF (xhtml2pdf)

**1_📅_Historique.py**
- Sélecteur date + filtres région/catégorie/secteur
- Affichage brief complet
- Export PDF

**2_🔥_Alertes.py**
- Timeline alertes chronologique
- Stats : MEGA_DEAL / FALLEN_ANGEL / PROFIT_WARNING
- Graphique hebdomadaire Plotly

**3_🌍_Heatmap.py**
- Heatmap Plotly secteur × géographie
- Mode Volume (nb news) ou Valeur (Md€ deals)
- Filtres période + catégorie
- Top 10 deals par montant
- Secteurs incluant `Commodities` dans l'ordre d'affichage

**4_🔍_Recherche.py**
- Recherche full-text (headline + summary + so_what + source)
- Filtres : date range, catégorie, région, source, secteur, fiabilité
- Surlignage mots-clés
- Export CSV standard + Export Bloomberg CSV

**5_📧_Abonnement.py** (ajouté)
- Formulaire d'inscription email (`src/subscribers.py`)
- Désinscription via formulaire ou URL `?unsubscribe=email`
- Liste des abonnés actuels
- Redirect depuis liens emails (`?page=abonnement`)

---

## 12. ABONNEMENTS EMAIL (subscribers.py)

```python
# data/subscribers.json
{"subscribers": ["user@example.com", ...]}
```

`emailer.get_recipients()` fusionne `RECIPIENTS` (env) + `data/subscribers.json` (dédupliqué).

Footer des emails contient un lien de désinscription → `{streamlit_url}?page=abonnement`.

---

## 13. MARKET SNAPSHOT (market_snapshot.py)

Fetche via `yfinance` au moment du brief :
- CAC 40, S&P 500, EUR/USD, EUR/GBP, Brent Oil, Gold

Stocké dans `brief["market_snapshot"]` et affiché en haut du dashboard et des emails.

---

## 14. FORMAT JSON ARCHIVE

### data/briefs/YYYY-MM-DD.json
```json
{
  "date": "2026-05-08",
  "generated_at": "2026-05-08T08:18:17.462642+02:00",
  "stats": {
    "collected": 1030,
    "verified": 869,
    "filtered": 467,
    "deduplicated": 467,
    "sent_to_llm": 80,
    "returned": 10,
    "post_verified": 9
  },
  "market_snapshot": {
    "CAC 40": {"value": "8202", "change": "-1.17%", "trend": "down"},
    "S&P 500": {"value": "7337", "change": "-0.38%", "trend": "down"}
  },
  "news": [
    {
      "rank": 1,
      "category": "M&A",
      "headline": "Titre en français",
      "source": "Reuters",
      "date": "2026-05-08",
      "url": "https://...",
      "sector": "Energy",
      "geography": "France",
      "region": "Europe",
      "deal_size_eur": 6500000000,
      "confidence": "high",
      "source_count": 3,
      "summary": "...",
      "so_what": "...",
      "alert_flags": []
    }
  ]
}
```

### data/alerts/YYYY-MM-DD.json
Même structure avec clé `"alerts"` au lieu de `"news"`. Alertes appendées au fur et à mesure, dédupliquées par URL.

---

## 15. WORKFLOWS GITHUB ACTIONS

### daily-brief.yml (7j/7 à 08h30 Paris)
```yaml
on:
  schedule:
    - cron: '30 6 * * *'   # UTC+2 (été)
    - cron: '30 7 * * *'   # UTC+1 (hiver)
  workflow_dispatch:

jobs:
  send-brief:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11', cache: 'pip'}
      - run: pip install -r requirements.txt
      - run: python -m src.main_brief
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          RECIPIENTS: ${{ secrets.RECIPIENTS }}
          STREAMLIT_URL: ${{ secrets.STREAMLIT_URL }}
          FORCE_SEND: false
      - name: Commit archive
        run: |
          git config user.name "Daily Brief Bot"
          git config user.email "bot@github-actions.local"
          git add data/
          git diff --staged --quiet || git commit -m "Brief $(date +%Y-%m-%d)"
          git pull --rebase || true
          git push
```

**Fenêtre d'envoi** : 08:25–08:45 Paris (guard dans `main_brief.py` pour éviter double-envoi entre les 2 crons UTC+1/UTC+2).

### hourly-alerts.yml (lun-ven 09h-19h)
```yaml
on:
  schedule:
    - cron: '5 7-17 * * 1-5'   # UTC+2
    - cron: '5 8-18 * * 1-5'   # UTC+1
```

**Fenêtre** : 09:00–19:30 Paris. Lookback 90 min. Déduplique par URL avant d'envoyer.

### monthly-rss-health.yml
Vérifie mensuellement que chaque source RSS répond. Log warning pour les morts.

**Budget Actions free tier** : ~880 min/mois (quota : 2000 min). Largement OK.

---

## 16. CONFIGURATION LOCALE

### .env (gitignorés — ne jamais committer)
```
GEMINI_API_KEY=AIzaSyDsU4kxUWhfrXWNpgtGWxPsOInopeaBGnM
GMAIL_USER=codjogahito@gmail.com
GMAIL_APP_PASSWORD=jqmgfmqtzqouflwk
RECIPIENTS=codjo.gahito@outlook.com,codjo.gahito@natixis.com
STREAMLIT_URL=https://daily-finance-brief-cib.streamlit.app
DASHBOARD_PASSWORD=
```

### .streamlit/secrets.toml (gitignorés)
Même variables en format TOML pour le dev local Streamlit.

### Lancement local
```bash
# Brief complet
FORCE_SEND=true python -m src.main_brief

# Alertes
FORCE_SEND=true python -m src.main_alerts

# Dashboard
streamlit run streamlit_app.py

# Tests
pytest tests/ -v

# Preview email
python scripts/preview_email.py
```

---

## 17. REQUIREMENTS

### requirements.txt (production)
```
feedparser==6.0.11
yfinance>=1.3.0
requests==2.32.3
google-genai>=1.0.0
python-dateutil==2.9.0.post0
pytz==2024.2
jinja2==3.1.4
beautifulsoup4==4.12.3
tenacity==9.0.0
streamlit>=1.38.0
pandas>=2.2.2
plotly>=5.24.0
xhtml2pdf==0.2.16
unidecode==1.3.8
lxml>=5.3.0
```

### packages.txt
Vide — `xhtml2pdf` utilise `reportlab` (pur Python) et n'a besoin d'aucune dépendance système. Les entrées `libpango`/`libcairo` précédentes étaient des dépendances WeasyPrint incorrectement incluses — elles cassaient le déploiement Streamlit Cloud.

---

## 18. TROUBLESHOOTING

### "Error installing requirements" sur Streamlit Cloud
→ Vérifier `packages.txt` : ne doit contenir AUCUN paquet apt qui n'existe pas dans l'Ubuntu de Streamlit Cloud. Si doute, vider le fichier — `xhtml2pdf` n'a pas besoin de dépendances système.

### Brief non reçu
1. `gh run list` → logs GitHub Actions
2. Vérifier spam Natixis (ajouter `codjogahito@gmail.com` en contact de confiance)
3. Tester en local : `FORCE_SEND=true python -m src.main_brief`

### Gemini JSON tronqué
→ `max_output_tokens` doit être ≥ 16000. Si tronqué, `_extract_json()` fail et le fallback prend le relais.

### So What affiche "[Analyse LLM indisponible...]"
→ Vérifier la clé `GEMINI_API_KEY`. Pour patcher des briefs existants : remplacer manuellement dans le JSON avec `_heuristic_so_what()`. Le filtre `news_card()` supprime maintenant l'affichage de ce message d'erreur.

### Liens articles brisés
→ GNews proxy URLs non résolvables en EU (consent.google.com). Solution implémentée : fallback Google Search (`https://www.google.com/search?q=headline+source`). Sources paywallées : badge "Accès abonné" + bouton "Rechercher".

### Streamlit Cloud ne redéploie pas
→ Vérifier que le `git push` du workflow a réussi. Branche : `master` (pas `main`). Délai normal : 2-3 min.

### Gemini quota dépassé
Free tier : 1500 req/jour, 15 req/min. Chaque brief = 1 req, chaque alerte = 1 req. Si quota : fallback `_fallback_selection()` automatique.

---

## 19. PERSONNALISATION RAPIDE

| Objectif | Fichier |
|---|---|
| Ajouter une source RSS | `src/collectors/sources.py` |
| Ajuster les mots-clés de filtre | `src/filters.py` — WHITELIST/BLACKLIST |
| Modifier les seuils alertes | `src/alert_detector.py` |
| Changer les heures d'envoi | `.github/workflows/daily-brief.yml` |
| Modifier le design emails | `src/templates/email_brief.html`, `email_alert.html` |
| Modifier le dashboard | `streamlit_app.py` + `pages/` |
| Ajouter un destinataire permanent | Modifier `RECIPIENTS` dans GitHub Secrets |
| Ajouter un destinataire via UI | Page Abonnement sur Streamlit |

---

## 20. HISTORIQUE DES MODIFICATIONS

| Date | Modification |
|---|---|
| Initial | Scaffold complet : RSS, Gemini, Gmail, Streamlit, GitHub Actions |
| Session 1 | Design système "Coffee Economics News" — Inter/Goldman Sans, sidebar foncée, cards propres |
| Session 2 | Fix So What (erreur LLM supprimée du rendu), fix liens GNews → Google Search fallback, fix Gemini JSON tronqué (max_output_tokens=16000), diversité fallback (max 2 items/source) |
| Session 2 | Ajout : Home button, sidebar toggle, page Abonnement (5_📧_Abonnement.py), subscribers.py, lien désinscription dans emails |
| Session 2 | Déploiement Streamlit Cloud (`https://daily-finance-brief-cib.streamlit.app`) |
| Session 3 | Fix "Error installing requirements" : vidage packages.txt (libpango/libcairo = dépendances WeasyPrint incorrectes), retrait pytest des requirements |
| Session 3 | Suppression stats pipeline (Collectées/Filtrées/Sélectionnées) de l'UI |
| 2026-05-08 | Ajout couverture Commodities : 6 nouvelles sources, secteur Commodities dans enrichment, ~20 keywords whitelist, critère #4 dans prompt Gemini, ordre heatmap |
