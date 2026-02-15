import streamlit as st
from datetime import date
from fpdf import FPDF
from PIL import Image
import os
import io
import json
import base64
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Tech-Report Pro", layout="wide", page_icon="🏗️")

# --- INITIALISATION DU SESSION STATE ---
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]
if 'client_name' not in st.session_state:
    st.session_state.client_name = ""
if 'adresse' not in st.session_state:
    st.session_state.adresse = ""
if 'technicien' not in st.session_state:
    st.session_state.technicien = ""

# --- FONCTIONS UTILITAIRES POUR LA SAUVEGARDE (BASE64) ---
def images_to_base64(sections):
    """Convertit les fichiers UploadedFile en texte pour le JSON."""
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    encoded = base64.b64encode(img.getvalue()).decode()
                    photos_data.append({"name": img.name, "type": img.type, "content": encoded})
                except:
                    continue
            new_sec['photos_base64'] = photos_data
        # On ne peut pas sérialiser les objets UploadedFile, on les retire de la copie
        if 'photos' in new_sec:
            del new_sec['photos']
        sections_copy.append(new_sec)
    return sections_copy

def base64_to_images(sections_data):
    """Convertit le texte Base64 du JSON en flux binaires exploitables."""
    for s in sections_data:
        if s.get('photos_base64'):
            restored_photos = []
            for p_data in s['photos_base64']:
                img_bytes = base64.b64decode(p_data['content'])
                buf = io.BytesIO(img_bytes)
                buf.name = p_data['name'] # Reconstruit l'attribut name
                restored_photos.append(buf)
            s['photos'] = restored_photos
    return sections_data

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .section-container { border: 1px solid #ddd; padding: 20px; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Générateur de Rapport Technique")

# --- BARRE LATÉRALE : SAUVEGARDE ET RESTAURATION ---
st.sidebar.header("💾 Gestion du Brouillon")

# Préparation des données de sauvegarde
data_to_save = {
    "client_name": st.session_state.client_name,
    "adresse": st.session_state.adresse,
    "technicien": st.session_state.technicien,
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}

st.sidebar.download_button(
    label="📥 Télécharger la sauvegarde (.json)",
    data=json.dumps(data_to_save, indent=4),
    file_name=f"sauvegarde_{st.session_state.client_name or 'rapport'}.json",
    mime="application/json"
)

st.sidebar.divider()
uploaded_brouillon = st.sidebar.file_uploader("📂 Charger un brouillon", type=["json"])

if uploaded_brouillon:
    if st.sidebar.button("♻️ Restaurer les données"):
        data = json.load(uploaded_brouillon)
        st.session_state.client_name = data.get("client_name", "")
        st.session_state.adresse = data.get("adresse", "")
        st.session_state.technicien = data.get("technicien", "")
        st.session_state.participants = data.get("participants", [])
        st.session_state.sections = base64_to_images(data.get("sections", []))
        st.rerun()

# --- ÉTAPE 1 : INFOS GÉNÉRALES ---
with st.expander("📌 Informations du Chantier", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.client_name = st.text_input("Nom du Client / Projet", value=st.session_state.client_name)
        st.session_state.adresse = st.text_input("Adresse de l'intervention", value=st.session_state.adresse)
    with col2:
        date_visite = st.date_input("Date de la visite", date.today())
        st.session_state.technicien = st.text_input("Technicien responsable", value=st.session_state.technicien)

# --- ÉTAPE 2 : PARTICIPANTS ---
st.header("👥 Participants")
if st.button("➕ Ajouter un participant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})

for i, p in enumerate(st.session_state.participants):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    p['nom'] = c1.text_input(f"Nom & Prénom", value=p['nom'], key=f"p_nom_{i}")
    p['tel'] = c2.text_input(f"Téléphone", value=p['tel'], key=f"p_tel_{i}")
    p['email'] = c3.text_input(f"Email", value=p['email'], key=f"p_email_{i}")
    if c4.button("🗑️", key=f"del_p_{i}"):
        st.session_state.participants.pop(i)
        st.rerun()

# --- ÉTAPE 3 : SECTIONS DU RAPPORT ---
st.header("📝 Corps du Rapport")
for idx, sec in enumerate(st.session_state.sections):
    with st.container():
        st.markdown(f"**Section {idx + 1}**")
        sec['titre'] = st.text_input("Titre", value=sec['titre'], key=f"sec_titre_{idx}")
        sec['description'] = st.text_area("Observations", value=sec['description'], key=f"sec_desc_{idx}")
        
        # Pour les photos restaurées, on affiche un indicateur car file_uploader ne peut pas être pré-rempli
        if sec.get('photos'):
            st.write(f"✅ {len(sec['photos'])} photo(s) chargée(s) pour cette section.")
            
        sec['photos'] = st.file_uploader(f"Ajouter/Remplacer photos (S{idx+1})", 
                                         accept_multiple_files=True, 
                                         type=['png', 'jpg', 'jpeg'], 
                                         key=f"sec_img_{idx}")
        
        if st.button(f"❌ Supprimer la section {idx+1}", key=f"del_sec_{idx}"):
            st.session_state.sections.pop(idx)
            st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})

# --- GÉNÉRATION WORD ---
def generate_word():
    doc = Document()
    doc.add_heading(f"RAPPORT : {st.session_state.client_name.upper()}", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    p = doc.add_paragraph()
    p.add_run(f"Date : {date_visite}\nTechnicien : {st.session_state.technicien}\nAdresse : {st.session_state.adresse}")

    doc.add_heading("Constats et Photos", level=1)
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    img_stream = io.BytesIO(img_file.getvalue())
                    doc.add_picture(img_stream, width=Inches(4.0))
                except:
                    continue
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- EXPORT FINAL ---
st.header("🏁 Exportation")
col_word, col_pdf = st.columns(2)

with col_word:
    if st.button("📝 Générer Word"):
        word_buf = generate_word()
        st.download_button(
            label="⬇️ Télécharger Word",
            data=word_buf.getvalue(),
            file_name=f"Rapport_{st.session_state.client_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
