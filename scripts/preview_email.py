"""Generate brief.html and alert.html locally for visual preview."""
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = ROOT / "src" / "templates"

MOCK_BRIEF = {
    "date": "2026-05-07",
    "generated_at": "2026-05-07T08:31:00+02:00",
    "stats": {"collected": 92, "verified": 78, "filtered": 45, "post_verified": 10},
    "low_volume": False,
    "news": [
        {
            "rank": 1,
            "category": "M&A",
            "headline": "KKR finalise le LBO de SunEnergy pour 6.5 Md€",
            "source": "Reuters",
            "date": "2026-05-07",
            "url": "https://reuters.com",
            "sector": "Energy",
            "geography": "France",
            "deal_size_eur": 6_500_000_000,
            "confidence": "high",
            "source_count": 3,
            "summary": "KKR et ses co-investisseurs ont finalisé l'acquisition de SunEnergy France, filiale renouvelable d'Engie, pour 6,5 milliards d'euros. La dette LBO est structurée en TLB 4,2x et un HY bond de €1,5 Md.",
            "so_what": "Transaction de référence pour le marché LevFin Q2 2026 : pricing tight à E+375 confirme l'appétit des investisseurs pour les actifs infrastructure. Watch: covenants maintenance vs. incurrence dans la doc.",
            "alert_flags": [],
        },
        {
            "rank": 2,
            "category": "LevFin",
            "headline": "Casino lance un refinancement HY de 2 Md€ post-restructuring",
            "source": "Les Echos Marchés",
            "date": "2026-05-07",
            "url": "https://lesechos.fr",
            "sector": "Consumer",
            "geography": "France",
            "deal_size_eur": 2_000_000_000,
            "confidence": "high",
            "source_count": 2,
            "summary": "Casino Group, sorti de sa procédure de conciliation en mars 2026, mandante Goldman Sachs et Natixis pour un refinancement obligataire HY de 2 milliards d'euros. Roadshow prévu la semaine prochaine.",
            "so_what": "Première fenêtre de marché post-distressed pour Casino : pricing attendu autour de 8-9% selon les sources. Mandat Natixis : à suivre pour le deal team.",
            "alert_flags": [],
        },
        {
            "rank": 3,
            "category": "Energy",
            "headline": "TotalEnergies signe un PPA de 15 ans avec Microsoft Azure",
            "source": "Reuters Energy",
            "date": "2026-05-07",
            "url": "https://reuters.com/energy",
            "sector": "Energy",
            "geography": "USA",
            "deal_size_eur": None,
            "confidence": "high",
            "source_count": 2,
            "summary": "TotalEnergies et Microsoft ont signé un Power Purchase Agreement (PPA) de 15 ans portant sur 500 MW d'énergie solaire aux États-Unis pour alimenter les data centers Azure. FID attendu en Q4 2026.",
            "so_what": "Template de financement corporate PPA : volumes en hausse tirés par l'IA. Structure project finance probable avec DSCR ≥1.3x sur back d'un offtake investment grade. Opportunité pipeline pour CIB.",
            "alert_flags": [],
        },
        {
            "rank": 4,
            "category": "Credit",
            "headline": "S&P dégrade Casino de BBB- à BB+ : fallen angel confirmé",
            "source": "S&P Ratings",
            "date": "2026-05-07",
            "url": "https://spglobal.com",
            "sector": "Consumer",
            "geography": "France",
            "deal_size_eur": None,
            "confidence": "high",
            "source_count": 4,
            "summary": "S&P Global a officiellement abaissé la note long terme de Casino Group de BBB- à BB+, perspective stable, suite à la finalisation du plan de restructuring. La note quitte l'univers Investment Grade.",
            "so_what": "Fallen angel avec sortie forcée des CLO IG et des mandats contraints investment grade : flush technique possible sur la dette Casino. Impact sur les spreads HY panier distribution/retail.",
            "alert_flags": [{"type": "FALLEN_ANGEL", "severity": "high", "reason": "Downgrade IG→HY"}],
        },
        {
            "rank": 5,
            "category": "Macro",
            "headline": "La BCE maintient ses taux à 4,5%, signal accommodant pour H2",
            "source": "ECB Press",
            "date": "2026-05-07",
            "url": "https://ecb.europa.eu",
            "sector": "Financials",
            "geography": "Other Europe",
            "deal_size_eur": None,
            "confidence": "high",
            "source_count": 5,
            "summary": "Le Conseil des gouverneurs de la BCE a maintenu le taux de la facilité de dépôt à 4,5%, conformément aux attentes du consensus. Christine Lagarde a indiqué deux baisses de taux possibles en H2 2026 si l'inflation reste sous 2,5%.",
            "so_what": "Signal favorable pour le refinancement des LBO à taux variable : les emprunteurs SOFR/EURIBOR voient leur charge d'intérêts allégée. Renforce l'appétit pour les actifs HY européens en duration.",
            "alert_flags": [],
        },
        {
            "rank": 6,
            "category": "Sector",
            "headline": "Rheinmetall remporte un contrat OTAN de 3,2 Md€",
            "source": "Bloomberg (GNews)",
            "date": "2026-05-07",
            "url": "https://bloomberg.com/rheinmetall",
            "sector": "Defense",
            "geography": "Germany",
            "deal_size_eur": 3_200_000_000,
            "confidence": "high",
            "source_count": 3,
            "summary": "Rheinmetall AG a remporté un contrat OTAN de livraison de 500 systèmes d'artillerie Lynx pour un montant de 3,2 milliards d'euros sur 5 ans. Livraisons débutent en Q2 2027.",
            "so_what": "Backlog défense record pour Rheinmetall (>35 Md€). Funding probable via Schuldscheindarlehen ou ECA-backed finance. Bon signal pour les émetteurs du secteur défense en DCM.",
            "alert_flags": [],
        },
        {
            "rank": 7,
            "category": "M&A",
            "headline": "Sanofi acquiert Inhibrx pour 2,5 Md$ en oncologie",
            "source": "WSJ Business",
            "date": "2026-05-06",
            "url": "https://wsj.com/sanofi",
            "sector": "Healthcare",
            "geography": "USA",
            "deal_size_eur": 2_300_000_000,
            "confidence": "high",
            "source_count": 2,
            "summary": "Sanofi annonce l'acquisition d'Inhibrx, biotech spécialisée en oncologie, pour 2,5 milliards de dollars cash. La transaction valorise Inhibrx à 35x l'EBITDA attendu 2027.",
            "so_what": "Multiple premium (35x) témoigne de la compétition pour les actifs oncologie de phase 3. Financement cash sans dette : bilan Sanofi solide (BBB+). Pattern M&A pharma : pipeline depletion force les acquéreurs.",
            "alert_flags": [],
        },
        {
            "rank": 8,
            "category": "Sector",
            "headline": "LVMH : résultats T1 en hausse de 8% malgré la prudence sur la Chine",
            "source": "Les Echos Marchés",
            "date": "2026-05-06",
            "url": "https://lesechos.fr/lvmh",
            "sector": "Luxury",
            "geography": "France",
            "deal_size_eur": None,
            "confidence": "high",
            "source_count": 3,
            "summary": "LVMH a publié un CA T1 2026 de 22,4 milliards d'euros, en hausse organique de 8%, porté par Mode & Maroquinerie (+11%). La division Asie-Pacifique reste sous pression (-3%) en raison du ralentissement de la consommation en Chine.",
            "so_what": "Résilience des marges LVMH (EBIT margin ~27%) : crédit stable, spread OAT+40bp justifié. Risque Chine limité : diversification géographique effective. Monitoring Q2 pour confirmation trend.",
            "alert_flags": [],
        },
        {
            "rank": 9,
            "category": "LevFin",
            "headline": "Altice France : restructuring imminent, accord en vue avec les créanciers",
            "source": "FT Companies",
            "date": "2026-05-07",
            "url": "https://ft.com/altice",
            "sector": "TMT",
            "geography": "France",
            "deal_size_eur": 24_000_000_000,
            "confidence": "medium",
            "source_count": 2,
            "summary": "Selon le Financial Times, Altice France et ses créanciers principaux sont proches d'un accord de restructuring portant sur 24 milliards d'euros de dette. Haircut attendu de 20-30% selon des sources proches du dossier (à confirmer).",
            "so_what": "Restructuring complexe : cascade intercreditor entre SSN, SUNs et RCF à surveiller. Opportunité distressed advisory. Watch: échange dette/equity et implication pour Drahi.",
            "alert_flags": [],
        },
        {
            "rank": 10,
            "category": "Geo",
            "headline": "Nouvelles sanctions US sur les exportations vers la Russie : impact pétrochimie",
            "source": "Reuters Business",
            "date": "2026-05-07",
            "url": "https://reuters.com/sanctions",
            "sector": "Energy",
            "geography": "USA",
            "deal_size_eur": None,
            "confidence": "medium",
            "source_count": 2,
            "summary": "Le Trésor américain a annoncé un nouveau paquet de sanctions ciblant 45 entités impliquées dans les exportations de produits pétrochimiques russes. Impact attendu sur les routes d'approvisionnement en Asie centrale (à confirmer).",
            "so_what": "Pression sur les prix du pétrochimique russe redirigé vers l'Asie : opportunité pour les producteurs MENA et européens. Watch: impact sur financing des routes alternatives et commodity trade finance.",
            "alert_flags": [],
        },
    ],
}

MOCK_ALERT = {
    "headline": "S&P dégrade Casino de BBB- à BB+ : fallen angel",
    "title": "S&P cuts Casino to junk status",
    "source": "S&P Ratings",
    "date": "2026-05-07",
    "published": "2026-05-07T10:15:00+00:00",
    "url": "https://spglobal.com/casino",
    "sector": "Consumer",
    "geography": "France",
    "deal_size_eur": None,
    "confidence": "high",
    "source_count": 4,
    "summary": "S&P Global Ratings a officiellement abaissé la note long terme de Casino Group de BBB- à BB+, avec perspective stable.",
    "so_what": "Fallen angel avec sortie forcée des CLO IG. Flush technique attendu sur la dette Casino.",
    "alert_flags": [{"type": "FALLEN_ANGEL", "severity": "high", "reason": "Downgrade IG→HY (fallen angel) détecté"}],
}


def main():
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

    # Generate brief.html
    brief_template = env.get_template("email_brief.html")
    brief_html = brief_template.render(
        brief=MOCK_BRIEF,
        streamlit_url="https://your-app.streamlit.app",
        generated_at=datetime.now().strftime("%d/%m/%Y à %H:%M"),
    )
    brief_path = ROOT / "brief.html"
    brief_path.write_text(brief_html, encoding="utf-8")
    print(f"[OK] Brief HTML genere : {brief_path}")

    # Generate alert.html
    alert_template = env.get_template("email_alert.html")
    alert_html = alert_template.render(
        item=MOCK_ALERT,
        alert_type="FALLEN_ANGEL",
        alert_reason="Downgrade IG→HY (fallen angel) détecté",
        streamlit_url="https://your-app.streamlit.app",
        generated_at=datetime.now().strftime("%d/%m/%Y à %H:%M"),
    )
    alert_path = ROOT / "alert.html"
    alert_path.write_text(alert_html, encoding="utf-8")
    print(f"[OK] Alert HTML genere : {alert_path}")

    # Open in browser
    try:
        webbrowser.open(brief_path.as_uri())
        webbrowser.open(alert_path.as_uri())
        print("[->] Ouverture dans le navigateur...")
    except Exception as e:
        print(f"⚠️ Impossible d'ouvrir le navigateur automatiquement : {e}")
        print(f"   → Ouvre manuellement : {brief_path}")

    print("\n[OK] Preview termine.")


if __name__ == "__main__":
    main()
