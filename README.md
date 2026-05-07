# Daily Finance Brief 📊

Système de veille financière automatisée — Coffee Economics News.

- **Brief quotidien** 7j/7 à 08h30 Paris par email
- **Alertes chaudes intraday** lun-ven 09h-19h (MEGA_DEAL >5Md€, fallen angel, profit warning ≥20%)
- **Dashboard Streamlit** : historique, heatmap deals, recherche full-text, export PDF
- **Coût additionnel** : 0€ (Gemini free tier, Gmail SMTP, GitHub Actions, Streamlit Community Cloud)

## Architecture

```
daily-finance-brief/
├── src/                    # Modules Python
│   ├── collectors/         # Collecte RSS parallélisée (~40 sources)
│   ├── filters.py          # Whitelist/blacklist + déduplication
│   ├── verifier.py         # URL alive, date, anti-spam
│   ├── enrichment.py       # Secteur, géo, deal_size_eur
│   ├── alert_detector.py   # Heuristiques alertes (no LLM)
│   ├── analyzer.py         # Gemini API (gemini-2.5-flash)
│   ├── emailer.py          # Gmail SMTP
│   ├── archiver.py         # JSON + git push
│   ├── main_brief.py       # Pipeline quotidien
│   └── main_alerts.py      # Pipeline horaire
├── streamlit_app.py        # Dashboard principal
├── pages/                  # Pages Streamlit multi-pages
├── data/                   # Archives JSON (committées par le bot)
├── tests/                  # Tests unitaires pytest
└── .github/workflows/      # GitHub Actions (daily + hourly)
```

## Setup initial (une seule fois)

### Prérequis
- Python 3.11+
- Compte GitHub (repo PUBLIC requis)
- Compte Google (pour Gemini API + Gmail App Password)
- Compte Streamlit Community Cloud

### 1. Installation locale

```bash
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Variables d'environnement (local)

```bash
cp .env.example .env
# Remplir .env avec vos clés
```

### 3. Preview email local

```bash
python scripts/preview_email.py
# Génère brief.html et alert.html et les ouvre dans le navigateur
```

### 4. Tests

```bash
pytest tests/ -v
```

### 5. GitHub Secrets (Phase 3)

```bash
gh secret set GEMINI_API_KEY --body "AIza..."
gh secret set GMAIL_USER --body "your@gmail.com"
gh secret set GMAIL_APP_PASSWORD --body "xxxx xxxx xxxx xxxx"
gh secret set RECIPIENTS --body "user1@outlook.com,user2@company.com"
gh secret set STREAMLIT_URL --body "https://your-app.streamlit.app"
```

## Lancement manuel

```bash
# Brief
FORCE_SEND=true python -m src.main_brief

# Alertes
FORCE_SEND=true python -m src.main_alerts
```

## GitHub Actions

- `daily-brief.yml` : 08h30 Paris, 7j/7
- `hourly-alerts.yml` : toutes les heures, lun-ven 09h-19h

**Budget Actions free tier** : ~880 min/mois (quota : 2000 min)

## Dashboard Streamlit

Pages disponibles :
1. **📊 Brief du jour** — Vue principale avec sélecteur de date
2. **📅 Historique** — Calendar picker + filtres + export PDF
3. **🔥 Alertes** — Timeline alertes chaudes + stats + graphique
4. **🌍 Heatmap** — Secteur × géographie en volume ou valeur
5. **🔍 Recherche** — Full-text + filtres avancés + export CSV

## Sources RSS (~40 sources)

- **Premium** : Reuters (5 feeds), FT (3), Bloomberg via GNews, WSJ, Economist (2)
- **Françaises** : Le Monde Économie, Les Echos (3), L'AGEFI
- **Banques centrales** : ECB, Fed, BoE
- **Ratings** : S&P, Moody's, Fitch via Google News
- **Deal flow** : M&A, LevFin, Energy Deals, PE/Buyouts, Restructuring via Google News
- **Sectoriels** : Defense, Tech, Aviation, Retail/Luxe, Entertainment, Healthcare, Real Estate

## Algorithme de sélection

1. Collecte parallèle (10 workers, timeout 15s/source)
2. Filtrage whitelist (>60 mots-clés CIB) + blacklist (sport, gossip, etc.)
3. Vérification URL + date (fenêtre 72h) + anti-spam
4. Déduplication (SequenceMatcher ratio >0.85, priorité FT/Reuters/Bloomberg)
5. Enrichissement automatique (secteur, géographie, montant en EUR)
6. Analyse Gemini (température 0.2, max 80 candidats envoyés)
7. Post-vérification anti-hallucination (montants vérifiés vs. source)

## Alertes chaudes (heuristiques, sans LLM)

- **MEGA_DEAL** : deal_size_eur ≥ 5Md€ + mots-clés deal
- **FALLEN_ANGEL** : downgrade IG→HY (patterns regex)
- **PROFIT_WARNING** : avertissement résultats ≥20%

## Personnalisation

| Fichier | Modification |
|---------|-------------|
| `src/collectors/sources.py` | Ajouter/supprimer des sources RSS |
| `src/filters.py` | Ajuster whitelist/blacklist |
| `src/alert_detector.py` | Modifier seuils alertes |
| `src/templates/email_*.html` | Changer le design des emails |
| `streamlit_app.py` | Modifier le dashboard |
| `.github/workflows/*.yml` | Changer les horaires |

## Troubleshooting

**Email non reçu ?**
1. Vérifier `gh run list` → logs GitHub Actions
2. Vérifier spam sur codjo.gahito@natixis.com (bloquer corporate possible → whitelister codjogahito@gmail.com)
3. Tester : `FORCE_SEND=true python -m src.main_brief`

**Gemini API quota dépassé ?**
- Free tier : 1500 req/jour, 15 req/min
- Chaque brief = 1 req, chaque alerte = 1 req
- Si quota dépassé : le pipeline bascule automatiquement sur la sélection fallback (sans LLM)

**Streamlit ne se met pas à jour ?**
- Vérifier que le git push du workflow a réussi
- Streamlit Cloud se re-déploie automatiquement sur push `main`
- Délai normal : 2-3 min après le push

**Sources RSS mortes ?**
- Un log warning est généré mais le pipeline continue
- Identifier les sources mortes dans les logs GitHub Actions
- Les désactiver dans `src/collectors/sources.py`

## FAQ

**Q: Pourquoi Python 3.11 dans GitHub Actions et non 3.14 ?**
A: Stabilité des dépendances (streamlit, pandas, weasyprint). Python 3.14 est disponible localement via uv.

**Q: Les briefs weekend sont-ils envoyés ?**
A: Oui — le cron est 7j/7 et la fenêtre lookback de 72h couvre le weekend sans gap.

**Q: Puis-je ajouter des destinataires ?**
A: Oui — modifier le secret GitHub `RECIPIENTS` (séparés par virgule).

**Q: Le dashboard est-il sécurisé ?**
A: Public par défaut (requis pour Streamlit free tier). Ajouter `DASHBOARD_PASSWORD` dans Streamlit Secrets pour activer un écran de login.
