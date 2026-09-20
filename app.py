"""Démo minimale du tri de demandes de support.

Usage : streamlit run app.py   (Ollama doit être lancé)
"""
import streamlit as st

from ai.interop_assistant import InvalidLLMResponseError, OllamaUnavailableError
from ai.ticket_triage import CATEGORIES, classify_ticket

st.title("Tri de demandes de support")
st.caption(
    "Le LLM choisit une catégorie dans une liste fixe ; Python rejette toute autre réponse. "
    "N'entre jamais de vraies données de patient."
)

ticket_text = st.text_area("Demande", placeholder="Ex. : la date de naissance est vide sur de nombreuses fiches")

if st.button("Classer la demande"):
    if not ticket_text.strip():
        st.warning("Écris une demande avant de lancer le tri.")
    else:
        try:
            with st.spinner("Analyse en cours..."):
                category = classify_ticket(ticket_text)
        except OllamaUnavailableError:
            st.error("Ollama est indisponible. Vérifie qu'il est lancé, puis réessaie.")
        except InvalidLLMResponseError:
            st.error("Le modèle a renvoyé une réponse invalide : elle a été rejetée.")
        else:
            st.success(f"Catégorie : {category}")
            st.write(CATEGORIES[category])
