import streamlit as st
from datetime import date, datetime
from fpdf import FPDF
from PIL import Image
import os
import io
import json
import base64
from docx import Document

# --- CONFIGURATION ---
st.set_page_config(page_title="Tech-Report Pro", layout="wide", page_icon="🏗️")

# --- INITIALISATION ---
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]

# Initialisation des infos générales
for key in ['cli_val', 'adr_val', 'tec_val']:
    if key not in st.session_state: st.session_state[key] = ""
if 'date_val' not in st.session_state: st.session_state['date_val'] = date.today()

# --- FONCTIONS DE CONVERSION ---
def images_to_base64(sections):
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    img_bytes = img.getvalue() if hasattr(img, 'getvalue') else img.read()
                    encoded = base64.b64encode(img_bytes).decode()
                    photos_data.append({"name": getattr(img, 'name', 'photo.jpg'), "content": encoded})
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
                try:
                    buf = io.BytesIO(base64.b64decode(p['content']))
                    buf.name = p['name']
                    restored.append(buf)
                except: continue
            s['photos'] = restored
    return sections_data

# --- GÉNÉRATION PDF ---
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "RAPPORT D'INTERVENTION", ln=True, align='C', fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)
    pdf.ln(5)
    def c(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 7, f"Client : {c(st.session_state.cli_val)}", ln=True)
    pdf.cell(0, 7, f"Adresse : {c(st.session_state.adr_val)}", ln=True)
    pdf.cell(0, 7, f"Date : {st.session_state.date_val.strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    for sec in st.session_state.sections:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, c(sec.get('titre', '')).upper(), ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 7, c(sec.get('description', '')))
        if sec.get('photos'):
            for i, img_file in enumerate(sec['photos']):
                try:
                    img = Image.open(io.BytesIO(img_file.getvalue()))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    path = f"tmp_{i}.jpg"
                    img.save(path, "JPEG")
                    if pdf.get_y() > 220: pdf.add_page()
                    pdf.image(path, w=100)
                    os.remove(path)
                except: continue
    return pdf.output()

# --- SIDEBAR : SAUVEGARDE & RESTAURATION ---
st.sidebar.header("💾 Gestion du Dossier")

save_dict = {
    "client_name": st.session_state.cli_val,
    "adresse": st.session_state.adr_val,
    "technicien": st.session_state.tec_val,
    "date_intervention": str(st.session_state.date_val),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder JSON", json.dumps(save_dict, indent=4), "sauvegarde.json")

uploaded = st.sidebar.file_uploader("📂 Charger JSON", type=["json"])

if uploaded and st.sidebar.button("♻️ RESTAURER LES DONNÉES"):
    data = json.load(uploaded)
    
    # NETTOYAGE DES CLÉS (Pour forcer la Section 1 à se mettre à jour)
    for key in list(st.session_state.keys()):
        if key.startswith(('t_', 'd_', 'cli_val', 'adr_val', 'tec_val', 'pnom_', 'ptel_', 'pmail_')):
            del st.session_state[key]
            
    # INJECTION DES DONNÉES
    st.session_state.cli_val = data.get("client_name", "")
    st.session_state.adr_val = data.get("adresse", "")
    st.session_state.tec_val = data.get("technicien", "")
    try:
        st.session_state.date_val = datetime.strptime(data.get("date_intervention"), "%Y-%m-%d").date()
    except:
        st.session_state.date_val = date.today()
    st.session_state.participants = data.get("participants", [])
    st.session_state.sections = base64_to_images(data.get("sections", []))
    
    st.rerun()

# --- INTERFACE ---
st.title("🏗️ Tech-Report Pro")

with st.expander("📌 Informations Chantier", expanded=True):
    st.text_input("Client", key="cli_val")
    st.text_input("Adresse", key="adr_val")
    st.text_input("Technicien", key="tec_val")
    st.date_input("Date", key="date_val")

st.header("👥 Participants")
if st.button("➕ Ajouter un participant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})
    st.rerun()

for i, p in enumerate(st.session_state.participants):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    p['nom'] = c1.text_input(f"Nom {i}", value=p.get('nom',''), key=f"pnom_{i}")
    p['tel'] = c2.text_input(f"Tél {i}", value=p.get('tel',''), key=f"ptel_{i}")
    p['email'] = c3.text_input(f"Email {i}", value=p.get('email',''), key=f"pmail_{i}")
    if c4.button("🗑️", key=f"pdel_{i}"):
        st.session_state.participants.pop(i)
        st.rerun()

st.header("📝 Corps du Rapport")



for idx, sec in enumerate(st.session_state.sections):
    with st.container():
        st.subheader(f"Section {idx+1}")
        
        # Le titre et la description sont liés aux données de st.session_state.sections
        st.session_state.sections[idx]['titre'] = st.text_input(
            f"Titre Section {idx+1}", 
            value=sec.get('titre', ''), 
            key=f"t_{idx}"
        )
        
        st.session_state.sections[idx]['description'] = st.text_area(
            f"Observations Section {idx+1}", 
            value=sec.get('description', ''), 
            key=f"d_{idx}"
        )
        
        if sec.get('photos'):
            st.info(f"📸 {len(sec['photos'])} photo(s) chargée(s)")
        
        new_imgs = st.file_uploader(f"Photos S{idx+1}", accept_multiple_files=True, key=f"img_{idx}")
        if new_imgs:
            st.session_state.sections[idx]['photos'] = new_imgs
            
        if st.button(f"🗑️ Supprimer Section {idx+1}", key=f"sdel_{idx}"):
            st.session_state.sections.pop(idx)
            st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})
    st.rerun()

if st.button("📄 Générer le Rapport PDF"):
    pdf_res = generate_pdf()
    st.download_button("⬇️ Télécharger PDF", bytes(pdf_res) if not isinstance(pdf_res, str) else pdf_res.encode('latin-1'), f"Rapport_{st.session_state.cli_val}.pdf", "application/pdf")
