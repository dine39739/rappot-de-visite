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

# --- CONFIGURATION ---
st.set_page_config(page_title="Tech-Report Pro", layout="wide", page_icon="🏗️")

# --- INITIALISATION ---
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]

# --- FONCTIONS DE CONVERSION ---
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
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    client = st.session_state.get('cl_val', 'RAPPORT')
    pdf.cell(0, 10, f"RAPPORT : {client.upper()}", ln=True, align='C')
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
                    temp = f"tmp_{idx}_{i}.jpg"
                    img.save(temp, "JPEG")
                    pdf.image(temp, w=80)
                    os.remove(temp)
                except: continue
    return pdf.output()

def generate_word():
    doc = Document()
    doc.add_heading("RAPPORT TECHNIQUE", 0)
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    doc.add_picture(io.BytesIO(img_file.getvalue()), width=Inches(3.5))
                except: continue
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- BARRE LATÉRALE : SAUVEGARDE ET RESTAURATION ---
st.sidebar.header("💾 Gestion")

# 1. Sauvegarde
save_obj = {
    "client_name": st.session_state.get('cl_val', ''),
    "adresse": st.session_state.get('ad_val', ''),
    "technicien": st.session_state.get('te_val', ''),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder JSON", json.dumps(save_obj), "sauvegarde.json")

# 2. Restauration
uploaded = st.sidebar.file_uploader("📂 Charger un fichier", type="json")
if uploaded and st.sidebar.button("♻️ RESTAURER MAINTENANT"):
    data = json.load(uploaded)
    # Nettoyage pour éviter les bugs Streamlit
    for k in list(st.session_state.keys()):
        if k.startswith(('t_','d_','pnom_','ptel_','pmail_','cl_','ad_','te_')):
            del st.session_state[k]
    
    # Remplissage du state
    st.session_state.client_name = data.get('client_name', '')
    st.session_state.adresse = data.get('adresse', '')
    st.session_state.technicien = data.get('technicien', '')
    st.session_state.participants = data.get('participants', [])
    st.session_state.sections = base64_to_images(data.get('sections', []))
    st.rerun()

# --- INTERFACE ---
st.title("🏗️ Tech-Report Pro")

with st.expander("📌 Infos Chantier", expanded=True):
    c1, c2 = st.columns(2)
    st.session_state.client_name = c1.text_input("Client", value=st.session_state.get('client_name',''), key="cl_val")
    st.session_state.adresse = c1.text_input("Adresse", value=st.session_state.get('adresse',''), key="ad_val")
    st.session_state.technicien = c2.text_input("Technicien", value=st.session_state.get('technicien',''), key="te_val")

st.header("👥 Intervenants")
if st.button("➕ Ajouter intervenant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})
    st.rerun()

for i, p in enumerate(st.session_state.participants):
    col = st.columns([3, 2, 3, 1])
    p['nom'] = col[0].text_input(f"Nom {i}", value=p.get('nom',''), key=f"pnom_{i}")
    p['tel'] = col[1].text_input(f"Tél {i}", value=p.get('tel',''), key=f"ptel_{i}")
    p['email'] = col[2].text_input(f"Email {i}", value=p.get('email',''), key=f"pmail_{i}")
    if col[3].button("🗑️", key=f"pdel_{i}"):
        st.session_state.participants.pop(i)
        st.rerun()

st.header("📝 Rapport")
for i, sec in enumerate(st.session_state.sections):
    with st.container():
        sec['titre'] = st.text_input(f"Titre S{i+1}", value=sec.get('titre',''), key=f"t_{i}")
        sec['description'] = st.text_area(f"Texte S{i+1}", value=sec.get('description',''), key=f"d_{i}")
        new_imgs = st.file_uploader(f"Photos S{i+1}", accept_multiple_files=True, key=f"img_{i}")
        if new_imgs: sec['photos'] = new_imgs
        if st.button(f"🗑️ Supprimer S{i+1}", key=f"del_{i}"):
            st.session_state.sections.pop(i)
            st.rerun()
        st.divider()

if st.button("➕ Ajouter Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})
    st.rerun()

# --- EXPORT ---
st.header("🏁 Export")
e1, e2 = st.columns(2)
with e1:
    if st.button("📄 PDF"):
        res = generate_pdf()
        st.download_button("Télécharger PDF", bytes(res) if not isinstance(res, str) else res.encode('latin-1'), "rapport.pdf", "application/pdf")
with e2:
    if st.button("📝 Word"):
        st.download_button("Télécharger Word", generate_word().getvalue(), "rapport.docx")
