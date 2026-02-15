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

# --- FONCTIONS TECHNIQUES (IMAGES & SAUVEGARDE) ---
def images_to_base64(sections):
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
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

# --- GÉNÉRATION DES DOCUMENTS ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 15, f"RAPPORT : {st.session_state.get('client_name', '').upper()}", ln=True, align='C')
    
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"Client : {st.session_state.get('client_name', '')}", ln=True)
    pdf.cell(0, 7, f"Adresse : {st.session_state.get('adresse', '')}", ln=True)
    pdf.ln(5)

    for idx, sec in enumerate(st.session_state.sections):
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 10, sec.get('titre', 'SANS TITRE').upper(), ln=True)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, sec.get('description', ''))
        
        if sec.get('photos'):
            for i, img_file in enumerate(sec['photos']):
                try:
                    img = Image.open(io.BytesIO(img_file.getvalue()))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    temp = f"temp_{idx}_{i}.jpg"
                    img.save(temp, "JPEG")
                    if pdf.get_y() > 220: pdf.add_page()
                    pdf.image(temp, w=80)
                    os.remove(temp)
                except: continue
    return pdf.output()

def generate_word():
    doc = Document()
    doc.add_heading(f"RAPPORT : {st.session_state.get('client_name', '')}", 0)
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        if s.get('photos'):
            for img_file in s['photos']:
                try: doc.add_picture(io.BytesIO(img_file.getvalue()), width=Inches(3.5))
                except: continue
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- BARRE LATÉRALE (SAUVEGARDE) ---
st.sidebar.header("💾 Brouillon")
save_dict = {
    "client_name": st.session_state.get('client_name', ''),
    "adresse": st.session_state.get('adresse', ''),
    "technicien": st.session_state.get('technicien', ''),
    "date_intervention": str(st.session_state.get('date_intervention', date.today())),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder", json.dumps(save_dict, indent=4), "brouillon.json")

uploaded = st.sidebar.file_uploader("📂 Charger JSON", type="json")
if uploaded and st.sidebar.button("♻️ RESTAURER"):
    d = json.load(uploaded)
    # On nettoie le session_state des anciennes clés de widgets
    for key in list(st.session_state.keys()):
        if key.startswith(('t_', 'd_', 'pnom_', 'ptel_', 'pmail_', 'client_val', 'adr_val')):
            del st.session_state[key]
    
    st.session_state.client_name = d.get('client_name', "")
    st.session_state.adresse = d.get('adresse', "")
    st.session_state.technicien = d.get('technicien', "")
    st.session_state.participants =
