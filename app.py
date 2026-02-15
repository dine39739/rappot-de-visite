import streamlit as st
from datetime import date, datetime
from fpdf import FPDF
from PIL import Image
import os
import io
import json
import base64
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURATION ---
st.set_page_config(page_title="Tech-Report Pro", layout="wide", page_icon="🏗️")

# --- INITIALISATION ---
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]

# --- FONCTIONS SAUVEGARDE / RESTAURATION ---
def images_to_base64(sections):
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    # Gère les objets UploadedFile et les objets BytesIO (restaurés)
                    encoded = base64.b64encode(img.getvalue()).decode()
                    photos_data.append({"name": getattr(img, 'name', 'img.jpg'), "content": encoded})
                except: continue
            new_sec['photos_base64'] = photos_data
        if 'photos' in new_sec: del new_sec['photos']
        sections_copy.append(new_sec)
    return sections_copy

def base64_to_images(sections_data):
    for s in sections_data:
        if s.get('photos_base64'):
            restored = []
            for p in s['photos_base64']:
                buf = io.BytesIO(base64.b64decode(p['content']))
                buf.name = p['name']
                restored.append(buf)
            s['photos'] = restored
    return sections_data

# --- GÉNÉRATIONS DOCUMENTS ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 15, f"RAPPORT : {st.session_state.get('client_name', '').upper()}", ln=True, align='C')
    
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"Client : {st.session_state.get('client_name', '')}", ln=True)
    pdf.cell(0, 7, f"Adresse : {st.session_state.get('adresse', '')}", ln=True)
    pdf.ln(10)

    for idx, sec in enumerate(st.session_state.sections):
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, sec.get('titre', '').upper(), ln=True)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, sec.get('description', ''))
        
        if sec.get('photos'):
            for i, img_file in enumerate(sec['photos']):
                try:
                    img = Image.open(io.BytesIO(img_file.getvalue()))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    temp = f"temp_{idx}_{i}.jpg"
                    img.save(temp, "JPEG")
                    pdf.image(temp, w=80)
                    os.remove(temp)
                except: continue
    return pdf.output()

# --- SIDEBAR ET RESTAURATION ---
st.sidebar.header("💾 Brouillon")

# Préparation données pour téléchargement
save_data = {
    "client_name": st.session_state.get('client_name', ''),
    "adresse": st.session_state.get('adresse', ''),
    "technicien": st.session_state.get('technicien', ''),
    "date_intervention": str(st.session_state.get('date_intervention', date.today())),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}

st.sidebar.download_button("📥 Télécharger Sauvegarde", json.dumps(save_data, indent=4), "brouillon.json")

uploaded = st.sidebar.file_uploader("📂 Charger un fichier JSON", type="json")

if uploaded and st.sidebar.button("♻️ RESTAURER MAINTENANT"):
    d = json.load(uploaded)
    
    # ÉTAPE CRUCIALE : On vide les clés des widgets pour forcer le rafraîchissement
    for key in list(st.session_state.keys()):
        if key.startswith(('t_', 'd_', 'pnom_', 'ptel_', 'pmail_', 'client_', 'adr_', 'tech_')):
            del st.session_state[key]
            
    # On injecte les données dans le session_state
    st.session_state.client_name = d.get('client_name', "")
    st.session_state.adresse = d.get('adresse', "")
    st.session_state.technicien = d.get('technicien', "")
    try:
        st.session_state.date_intervention = datetime.strptime(d.get("date_intervention"), "%Y-%m-%d").date()
    except:
        st.session_state.date_intervention = date.today()
        
    st.session_state.participants = d.get('participants', [])
    st.session_state.sections = base64_to_images(d.get('sections', []))
    
    st.sidebar.success("Données chargées ! La page va s'actualiser...")
    st.rerun()

# --- INTERFACE ---
st.title("🏗️ Tech-Report Pro")

with st.expander("📌 Infos Chantier", expanded=True):
    col1, col2 = st.columns(2)
    # On lie directement la valeur au session_state
    c_name = col1.text_input("Client", value=st.session_state.get('client_name', ''), key="client_val")
    st.session_state.client_name = c_name
    
    adr = col1.text_input("Adresse", value=st.session_state.get('adresse', ''), key="adr_val")
    st.session_state.adresse = adr
    
    dt = col2.date_input("Date", value=st.session_state.get('date_intervention', date.today()), key="dt_val")
    st.session_state.date_intervention = dt
    
    tch = col2.text_input("Technicien", value=st.session_state.get('technicien', ''), key="tech_val")
    st.session_state.technicien = tch

st.header("👥 Intervenants")
if st.button("➕ Ajouter un intervenant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})
    st.rerun()

for i, p in enumerate(st.session_state.participants):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    p['nom'] = c1.text_input(f"Nom {i}", value=p['nom'], key=f"pnom_{i}")
    p['tel'] = c2.text_input(f"Tél {i}", value=p['tel'], key=f"ptel_{i}")
    p['email'] = c3.text_input(f"Email {i}", value=p['email'], key=f"pmail_{i}")
    if c4.button("🗑️", key=f"pdel_{i}"):
        st.session_state.participants.pop(i)
        st.rerun()

st.header("📝 Corps du Rapport")
for i, sec in enumerate(st.session_state.sections):
    with st.container():
        # ICI : On s'assure que la valeur affichée est celle du session_state
        sec['titre'] = st.text_input(f"Titre Section {i+1}", value=sec.get('titre', ''), key=f"t_{i}")
        sec['description'] = st.text_area(f"Observations Section {i+1}", value=sec.get('description', ''), key=f"d_{i}")
        
        if sec.get('photos'):
            st.info(f"📸 {len(sec['photos'])} photo(s) chargée(s)")
            
        new_photos = st.file_uploader(f"Photos S{i+1}", accept_multiple_files=True, type=['jpg','png'], key=f"img_{i}")
        if new_photos:
            sec['photos'] = new_photos
            
        if st.button(f"🗑️ Supprimer Section {i+1}", key=f"del_{i}"):
            st.session_state.sections.pop(i)
            st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})
    st.rerun()

# --- EXPORTS ---
st.
