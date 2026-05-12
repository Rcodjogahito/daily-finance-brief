"""Page 5 — Gestion des abonnements email."""
import streamlit as st

from src.styles import inject_css, sidebar_brand, page_toolbar
from src.subscribers import add_subscriber, remove_subscriber, load_subscribers

st.set_page_config(page_title="Abonnement — Daily Finance Brief", page_icon="", layout="wide")
inject_css()
sidebar_brand()
page_toolbar()

st.markdown(
    '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:5px">Coffee Economics News</div>',
    unsafe_allow_html=True,
)
st.title("Abonnement email")

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

st.markdown("---")

col1, col2 = st.columns(2)

# ── Subscribe ──────────────────────────────────────────────────────────────
with col1:
    st.markdown(
        '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:12px">S\'inscrire</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:13px;color:#374151;margin-bottom:16px;line-height:1.6">'
        'Recevez le Daily Finance Brief chaque matin à 08h30 et les alertes intraday directement dans votre boîte mail.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form("subscribe_form"):
        email_sub = st.text_input("Adresse email", placeholder="prenom.nom@banque.com")
        submitted = st.form_submit_button("S'inscrire")
        if submitted:
            if email_sub:
                ok, msg = add_subscriber(email_sub)
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.warning(msg)
            else:
                st.error("Veuillez saisir une adresse email.")

# ── Unsubscribe ────────────────────────────────────────────────────────────
with col2:
    st.markdown(
        '<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:12px">Se désinscrire</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:13px;color:#374151;margin-bottom:16px;line-height:1.6">'
        'Pour arrêter de recevoir les emails, saisissez votre adresse et confirmez la désinscription.'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.form("unsubscribe_form"):
        email_unsub = st.text_input("Adresse email", placeholder="prenom.nom@banque.com", key="unsub")
        submitted_u = st.form_submit_button("Se désinscrire")
        if submitted_u:
            if email_unsub:
                ok, msg = remove_subscriber(email_unsub)
                if ok:
                    st.success(f"✓ {msg}")
                else:
                    st.warning(msg)
            else:
                st.error("Veuillez saisir une adresse email.")

# ── Current list (admin view) ──────────────────────────────────────────────
st.markdown("---")
subscribers = load_subscribers()
st.markdown(
    f'<div style="font-size:8px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9A84C;margin-bottom:8px">{len(subscribers)} abonné(s)</div>',
    unsafe_allow_html=True,
)
if subscribers:
    for email in subscribers:
        st.markdown(
            f'<div style="font-size:13px;color:#374151;padding:4px 0;border-bottom:1px solid #F3F4F6">{email}</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("Aucun abonné pour le moment.")
