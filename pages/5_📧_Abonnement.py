"""Page 5 — Gestion des abonnements email."""
import streamlit as st

from src.styles import inject_css, sidebar_brand, section_header
from src.subscribers import add_subscriber, remove_subscriber, load_subscribers

st.set_page_config(
    page_title="Abonnement — Daily Finance Brief",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

# ── Sidebar nav ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("### Navigation")
    st.page_link("streamlit_app.py",              label="📰  Brief du jour")
    st.page_link("pages/1_📅_Historique.py",      label="📅  Historique")
    st.page_link("pages/2_🔥_Alertes.py",         label="🔥  Alertes intraday")
    st.page_link("pages/3_🌍_Heatmap.py",         label="🌍  Heatmap deals")
    st.page_link("pages/4_🔍_Recherche.py",        label="🔍  Recherche")
    st.page_link("pages/5_📧_Abonnement.py",       label="📧  Abonnement")
    st.markdown("---")

# ── Handle unsubscribe via query param (?page=abonnement&unsubscribe=email)
params = st.query_params
auto_email = params.get("unsubscribe", "")
if auto_email:
    ok, msg = remove_subscriber(auto_email)
    if ok:
        st.success(f"✓ {msg}")
    else:
        st.warning(msg)
    st.query_params.clear()

# ── Header ─────────────────────────────────────────────────────────────────
section_header("Coffee Economics News")
st.title("Abonnement email")
st.markdown(
    '<div style="font-size:14px;color:#6B7A8E;margin-top:-4px;margin-bottom:24px">'
    'Recevez le Daily Finance Brief chaque matin à 08h30'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# ── Infos ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(135deg,#07192E 0%,#0B2545 100%);'
    'border-radius:8px;padding:24px 28px;margin-bottom:28px;'
    'border:1px solid rgba(201,168,76,0.2)">'
    '<div style="font-size:8px;font-weight:700;letter-spacing:3px;'
    'text-transform:uppercase;color:#C9A84C;margin-bottom:12px">'
    'Ce que vous recevez</div>'
    '<div style="color:#C9D8E8;font-size:14px;line-height:1.8">'
    '📊 <strong style="color:#EEF5FF">Daily Finance Brief</strong> — '
    'Sélection des 10 news CIB les plus importantes, analysées par IA<br>'
    '⏰ <strong style="color:#EEF5FF">Chaque matin à 08h30</strong> — '
    'Directement dans votre boîte mail, 7j/7<br>'
    '🔬 <strong style="color:#EEF5FF">Analyse d\'impact Gemini</strong> — '
    'So what ? structuré niveau banquier senior pour chaque news<br>'
    '📈 <strong style="color:#EEF5FF">Marchés en temps réel</strong> — '
    'Snapshot EUR/USD, Brent, CAC40, Bund inclus'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

# ── Subscribe ──────────────────────────────────────────────────────────────
with col1:
    section_header("S'inscrire")
    st.markdown(
        '<div style="font-size:13px;color:#6B7A8E;margin-bottom:20px;line-height:1.7">'
        'Ajoutez votre email pour recevoir le brief quotidien. '
        'Désabonnement en un clic depuis chaque email.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form("subscribe_form"):
        email_sub = st.text_input(
            "Adresse email",
            placeholder="prenom.nom@banque.com",
        )
        submitted = st.form_submit_button("S'inscrire →", use_container_width=True)
        if submitted:
            if email_sub:
                ok, msg = add_subscriber(email_sub)
                if ok:
                    st.success(f"✓ {msg}")
                    st.balloons()
                else:
                    st.warning(f"⚠ {msg}")
            else:
                st.error("Veuillez saisir une adresse email.")

# ── Unsubscribe ────────────────────────────────────────────────────────────
with col2:
    section_header("Se désinscrire")
    st.markdown(
        '<div style="font-size:13px;color:#6B7A8E;margin-bottom:20px;line-height:1.7">'
        'Pour arrêter de recevoir les emails, saisissez votre adresse et confirmez. '
        'Vous pouvez aussi cliquer sur le lien de désinscription dans chaque email.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form("unsubscribe_form"):
        email_unsub = st.text_input(
            "Adresse email",
            placeholder="prenom.nom@banque.com",
            key="unsub",
        )
        submitted_u = st.form_submit_button("Se désinscrire", use_container_width=True)
        if submitted_u:
            if email_unsub:
                ok, msg = remove_subscriber(email_unsub)
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.warning(f"⚠ {msg}")
            else:
                st.error("Veuillez saisir une adresse email.")

# ── Current list ───────────────────────────────────────────────────────────
st.markdown("---")
subscribers = load_subscribers()
section_header(f"{len(subscribers)} abonné{'s' if len(subscribers) != 1 else ''}")

if subscribers:
    for i, email in enumerate(subscribers):
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:10px 14px;background:#FFFFFF;border:1px solid #E8EEF5;'
            f'border-radius:4px;margin-bottom:4px">'
            f'<span style="font-size:13px;color:#374151;font-weight:500">{email}</span>'
            f'<span style="font-size:10px;color:#9CA3AF;font-weight:500">#{i+1}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<div style="background:#F9FAFB;border-radius:6px;padding:20px;'
        'text-align:center;border:1px dashed #D1D5DB">'
        '<div style="font-size:24px;margin-bottom:8px">📭</div>'
        '<div style="font-size:13px;color:#9CA3AF">'
        'Aucun abonné via le formulaire pour le moment.<br>'
        '<span style="font-size:12px">Les destinataires configurés par l\'administrateur '
        'ne sont pas affichés ici.</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption(
    "🔒 Les adresses email sont stockées localement dans le dépôt Git (data/subscribers.json). "
    "Elles ne sont pas partagées avec des tiers."
)
