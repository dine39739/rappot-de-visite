import streamlit as st
from datetime import date

st.title("🛠️ Mon Tech-Report Personnel")

# --- FORMULAIRE DE RAPPORT ---
with st.form("report_form"):
    st.header("Informations de l'intervention")
    client_name = st.text_input("Nom du Client")
    intervention_date = st.date_input("Date", date.today())
    
    st.subheader("Détails")
    problem = st.text_area("Problème identifié")
    solution = st.text_area("Travaux réalisés")
    
    photos = st.file_uploader("Ajouter des photos", accept_multiple_files=True)
    
    submit = st.form_submit_button("Générer et Sauvegarder le Rapport")

if submit:
    # 1. Génération logique du texte
    report_content = f"Rapport pour {client_name}\nDate: {intervention_date}\n\nProblème: {problem}\nSolution: {solution}"
    
    st.success("Rapport généré avec succès !")
    
    # 2. Bouton de téléchargement (En attendant la liaison Drive)
    st.download_button("Télécharger le PDF", data=report_content, file_name=f"Rapport_{client_name}.txt")
