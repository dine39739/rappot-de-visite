import streamlit as st
from datetime import date
from fpdf import FPDF
from PIL import Image
import os
import io
import json
import base64
import urllib.parse
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

# --- FONCTIONS DE SAUVEGARDE (BASE64) ---
def images_to_base64(sections):
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    # On lit les octets directement depuis l'objet UploadedFile ou BytesIO
                    encoded = base64.b64encode(img.getvalue()).decode()
                    photos_data.append({"name": getattr(img, 'name', 'photo.jpg'), "type": getattr(img, 'type', 'image/jpeg'), "content": encoded})
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
                img_bytes = base64.b64decode(p['content'])
                buf = io.BytesIO(img_bytes)
                buf.name = p['name']
                buf.type = p['type']
                restored.append(buf)
            s['photos'] = restored
    return sections_data

# --- FONCTION GÉNÉRATION PDF ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Utilisation d'une police standard si DejaVu n'est pas dispo, sinon configurer DejaVu
    pdf.set_font("helvetica", 'B', 16)
    
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=30)
    
    pdf.ln(20)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, f"RAPPORT : {st.session_state.client_name.upper()}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", '', 10)
    pdf.ln(5)
    pdf.cell(0, 7, f"Client : {st.session_state.client_name}", ln=True)
    pdf.cell(0, 7, f"Adresse : {st.session_state.adresse}", ln=True)
    pdf.cell(0, 7, f"Technicien : {st.session_state.technicien}", ln=True)
    pdf.ln(10)

    for sec in st.session_state.sections:
        pdf.set_font("helvetica", 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, sec.get('titre', 'Sans titre').upper(), ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, sec.get('description', ''))
        
        if sec.get('photos'):
            for img_file in sec['photos']:
                try:
                    img = Image.open(img_stream := io.BytesIO(img_file.getvalue()))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    temp_name = f"temp_{img_file.name}"
                    img.save(temp_name)
                    if pdf.get_y() > 200: pdf.add_page()
                    pdf.image(temp_name, w=100)
                    pdf.ln(5)
                    os.remove(temp_name)
                except: continue
        pdf.ln(5)
    return pdf.output()

# --- FONCTION GÉNÉRATION WORD ---
def generate_word():
    doc = Document()
    doc.add_heading(f"RAPPORT : {st.session_state.client_name.upper()}", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Client : {st.session_state.client_name}\nAdresse : {st.session_state.adresse}\nTechnicien : {st.session_state.technicien}")
    
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=1)
        doc.add_paragraph(s.get('description', ''))
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    doc.add_picture(io.BytesIO(img_file.getvalue()), width=Inches(4.0))
                except: continue
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFACE STREAMLIT ---
st.sidebar.header("💾 Brouillon (Inclus Photos)")
save_data = {
    "client_name": st.session_state.client_name, "adresse": st.session_state.adresse,
    "technicien": st.session_state.technicien, "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder", json.dumps(save_data), f"brouillon_{st.session_state.client_name}.json")

uploaded = st.sidebar.file_uploader("📂 Charger", type="json")
if uploaded and st.sidebar.button("♻️ Restaurer"):
    d = json.load(uploaded)
    st.session_state.update({"client_name": d['client_name'], "adresse": d['adresse'], "technicien": d['technicien'], 
                             "participants": d['participants'], "sections": base64_to_images(d['sections'])})
    st.rerun()

# --- FORMULAIRE ---
with st.expander("📌 Infos Chantier", expanded=True):
    col1, col2 = st.columns(2)
    st.session_state.client_name = col1.text_input("Client", st.session_state.client_name)
    st.session_state.adresse = col1.text_input("Adresse", st.session_state.adresse)
    st.session_state.technicien = col2.text_input("Technicien", st.session_state.technicien)

st.header("📝 Corps du Rapport")
for i, sec in enumerate(st.session_state.sections):
    with st.container():
        sec['titre'] = st.text_input(f"Titre S{i+1}", sec['titre'], key=f"t{i}")
        sec['description'] = st.text_area(f"Observations S{i+1}", sec['description'], key=f"d{i}")
        if sec.get('photos'): st.info(f"📸 {len(sec['photos'])} photo(s) en mémoire")
        sec['photos'] = st.file_uploader(f"Photos S{i+1}", accept_multiple_files=True, type=['jpg','png'], key=f"img{i}")
        if st.button(f"🗑️ Supprimer S{i+1}", key=f"del{i}"):
            st.session_state.sections.pop(i)
            st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})
    st.rerun()

# --- EXPORT FINAL ---
st.header("🏁 Exportation")
c_pdf, c_word = st.columns(2)

with c_pdf:
    if st.button("📄 Générer PDF"):
        pdf_bytes = generate_pdf()
        st.download_button("⬇️ Télécharger PDF", pdf_bytes, f"Rapport_{st.session_state.client_name}.pdf", "application/pdf")

with c_word:
    if st.button("📝 Générer Word"):
        word_buf = generate_word()
        st.download_button("⬇️ Télécharger Word", word_buf.getvalue(), f"Rapport_{st.session_state.client_name}.docx")
