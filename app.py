import streamlit as st
from datetime import date
from fpdf import FPDF
import io
from PIL import Image

# Configuration de la page
st.set_page_config(page_title="Tech-Report Pro", layout="wide")

# Initialisation des états (Session State) pour le dynamisme
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]

st.title("🏗️ Générateur de Rapport Technique Pro")

# --- SECTION 1 : INFOS GÉNÉRALES ---
with st.expander("📌 Informations Générales", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Nom du Client / Projet")
        chantier_adresse = st.text_input("Adresse du chantier")
    with col2:
        intervention_date = st.date_input("Date de visite", date.today())
        technicien = st.text_input("Technicien responsable")

---

# --- SECTION 2 : PERSONNES PRÉSENTES ---
st.header("👥 Participants à la visite")
def ajouter_participant():
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})

if st.button("➕ Ajouter un participant"):
    ajouter_participant()

for i, p in enumerate(st.session_state.participants):
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
        p['nom'] = c1.text_input(f"Nom/Prénom", value=p['nom'], key=f"p_nom_{i}")
        p['tel'] = c2.text_input(f"Téléphone", value=p['tel'], key=f"p_tel_{i}")
        p['email'] = c3.text_input(f"Email", value=p['email'], key=f"p_email_{i}")
        if c4.button("🗑️", key=f"del_p_{i}"):
            st.session_state.participants.pop(i)
            st.rerun()

---

# --- SECTION 3 : CORPS DU RAPPORT (SECTIONS DYNAMIQUES) ---
st.header("📝 Observations et Photos")

def ajouter_section():
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})

for idx, sec in enumerate(st.session_state.sections):
    with st.container(border=True):
        st.subheader(f"Section {idx + 1}")
        sec['titre'] = st.text_input("Titre de la section (ex: État de la toiture)", value=sec['titre'], key=f"sec_titre_{idx}")
        sec['description'] = st.text_area("Description détaillée", value=sec['description'], key=f"sec_desc_{idx}")
        sec['photos'] = st.file_uploader(f"Photos pour Section {idx+1}", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'], key=f"sec_img_{idx}")
        
        if st.button(f"Supprimer la section {idx+1}", key=f"del_sec_{idx}"):
            st.session_state.sections.pop(idx)
            st.rerun()

if st.button("➕ Ajouter une nouvelle section"):
    ajouter_section()

---

# --- SECTION 4 : GÉNÉRATION DU PDF ---
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Header
    pdf.cell(190, 10, f"RAPPORT TECHNIQUE : {client_name}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(190, 10, f"Date : {intervention_date} | Technicien : {technicien}", ln=True, align='C')
    pdf.ln(10)

    # Participants
    if st.session_state.participants:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "Participants :", ln=True)
        pdf.set_font("Arial", size=10)
        for p in st.session_state.participants:
            pdf.cell(190, 7, f"- {p['nom']} | Tel: {p['tel']} | Email: {p['email']}", ln=True)
        pdf.ln(5)

    # Contenu des sections
    for sec in st.session_state.sections:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, sec['titre'], ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(190, 7, sec['description'])
        
        # Ajout des images
        if sec['photos']:
            for img_file in sec['photos']:
                # Traitement image pour le PDF
                img = Image.open(img_file)
                # On sauvegarde temporairement en bytes pour FPDF
                img_path = f"temp_{img_file.name}"
                img.save(img_path)
                pdf.image(img_path, w=80) # Largeur 80mm
                pdf.ln(2)

        pdf.ln(10)

    return pdf.output(dest='S')

if st.button("🚀 Générer le Rapport Final"):
    if not client_name:
        st.error("Veuillez au moins saisir le nom du client.")
    else:
        pdf_bytes = create_pdf()
        st.success("PDF Généré !")
        st.download_button(
            label="⬇️ Télécharger le Rapport PDF",
            data=pdf_bytes,
            file_name=f"Rapport_{client_name}_{intervention_date}.pdf",
            mime="application/pdf"
        )
