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
if 'client_name' not in st.session_state:
    st.session_state.client_name = ""
if 'adresse' not in st.session_state:
    st.session_state.adresse = ""
if 'technicien' not in st.session_state:
    st.session_state.technicien = ""
if 'date_intervention' not in st.session_state:
    st.session_state.date_intervention = date.today()

# --- FONCTIONS SAUVEGARDE ---
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

# --- GÉNÉRATION PDF ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, f"RAPPORT : {st.session_state.client_name.upper()}", ln=True, align='C', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", '', 10)
    pdf.ln(5)
    pdf.cell(0, 7, f"Client : {st.session_state.client_name}", ln=True)
    pdf.cell(0, 7, f"Adresse : {st.session_state.adresse}", ln=True)
    pdf.cell(0, 7, f"Date : {st.session_state.date_intervention}", ln=True)
    pdf.cell(0, 7, f"Technicien : {st.session_state.technicien}", ln=True)

    if st.session_state.participants:
        pdf.ln(5); pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, "PARTICIPANTS :", ln=True)
        pdf.set_font("helvetica", '', 10)
        for p in st.session_state.participants:
            pdf.cell(0, 7, f"- {p['nom']} ({p['tel']})", ln=True)

    for idx, sec in enumerate(st.session_state.sections):
        pdf.ln(10); pdf.set_font("helvetica", 'B', 14); pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, sec.get('titre', 'Sans titre').upper(), ln=True)
        pdf.set_text_color(0, 0, 0); pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 7, sec.get('description', ''))
        if sec.get('photos'):
            for i, img_file in enumerate(sec['photos']):
                try:
                    img = Image.open(io.BytesIO(img_file.getvalue()))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    temp = f"temp_img_{idx}_{i}.jpg"
                    img.save(temp, "JPEG")
                    if pdf.get_y() > 220: pdf.add_page()
                    pdf.image(temp, w=100)
                    os.remove(temp)
                except: continue
    return pdf.output()

# --- GÉNÉRATION WORD ---
def generate_word():
    doc = Document()
    doc.add_heading(f"RAPPORT : {st.session_state.client_name}", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Client : {st.session_state.client_name}\nAdresse : {st.session_state.adresse}\nDate : {st.session_state.date_intervention}")
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

# --- SIDEBAR ---
st.sidebar.header("💾 Brouillon")
save_data = {
    "client_name": st.session_state.client_name,
    "adresse": st.session_state.adresse,
    "technicien": st.session_state.technicien,
    "date_intervention": str(st.session_state.date_intervention),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder", json.dumps(save_data, indent=4), f"brouillon.json")

uploaded = st.sidebar.file_uploader("📂 Charger", type="json")
if uploaded and st.sidebar.button("♻️ Restaurer"):
    d = json.load(uploaded)
    # Nettoyage des clés pour éviter les conflits d'interface
    for key in list(st.session_state.keys()):
        if key.startswith(('t', 'd', 'pnom', 'ptel', 'pmail')):
            del st.session_state[key]
            
    restored_date = datetime.strptime(d.get("date_intervention", str(date.today())), "%Y-%m-%d").date()
    st.session_state.client_name = d.get('client_name', "")
    st.session_state.adresse = d.get('adresse', "")
    st.session_state.technicien = d.get('technicien', "")
    st.session_state.date_intervention = restored_date
    st.session_state.participants = d.get('participants', [])
    st.session_state.sections = base64_to_images(d.get('sections', []))
    st.rerun()

# --- INTERFACE ---
with st.expander("📌 Infos Chantier", expanded=True):
    col1, col2 = st.columns(2)
    st.session_state.client_name = col1.text_input("Client", st.session_state.client_name)
    st.session_state.adresse = col1.text_input("Adresse", st.session_state.adresse)
    st.session_state.date_intervention = col2.date_input("Date", st.session_state.date_intervention)
    st.session_state.technicien = col2.text_input("Technicien", st.session_state.technicien)

st.header("👥 Intervenants")
if st.button("➕ Ajouter un intervenant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})

for i, p in enumerate(st.session_state.participants):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    p['nom'] = c1.text_input("Nom", p['nom'], key=f"pnom{i}")
    p['tel'] = c2.text_input("Tél", p['tel'], key=f"ptel{i}")
    p['email'] = c3.text_input("Email", p['email'], key=f"pmail{i}")
    if c4.button("🗑️", key=f"pdel{i}"):
        st.session_state.participants.pop(i); st.rerun()

st.header("📝 Corps du Rapport")
for i, sec in enumerate(st.session_state.sections):
    with st.container():
        # Utilisation des clés pour lier les données au session_state
        sec['titre'] = st.text_input(f"Titre S{i+1}", sec['titre'], key=f"t{i}")
        sec['description'] = st.text_area(f"Observations S{i+1}", sec['description'], key=f"d{i}")
        if sec.get('photos'): st.info(f"📸 {len(sec['photos'])} photo(s) chargée(s)")
        new_photos = st.file_uploader(f"Ajouter photos S{i+1}", accept_multiple_files=True, type=['jpg','png'], key=f"img{i}")
        if new_photos: sec['photos'] = new_photos # Mise à jour si nouvelles photos
        
        if st.button(f"🗑️ Supprimer Section {i+1}", key=f"del{i}"):
            st.session_state.sections.pop(i); st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []}); st.rerun()

# --- EXPORT ---
st.header("🏁 Exportation")
c1, c2 = st.columns(2)
with c1:
    if st.button("📄 Générer PDF"):
        res = generate_pdf()
        st.download_button("⬇️ Télécharger PDF", bytes(res) if not isinstance(res, str) else res.encode('latin-1'), f"Rapport_{st.session_state.client_name}.pdf", "application/pdf")
with c2:
    if st.button("📝 Générer Word"):
        st.download_button("⬇️ Télécharger Word", generate_word().getvalue(), f"Rapport_{st.session_state.client_name}.docx")
