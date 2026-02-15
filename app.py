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
if 'date_visite' not in st.session_state:
    st.session_state.date_visite = date.today()

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES : SAUVEGARDE ET IMAGES ---
def images_to_base64(sections):
    """Convertit les images en texte pour le fichier de sauvegarde JSON."""
    sections_copy = []
    for s in sections:
        new_sec = s.copy()
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    if hasattr(img, 'getvalue'):
                        img_bytes = img.getvalue()
                    else:
                        img_bytes = img.read()
                    encoded = base64.b64encode(img_bytes).decode()
                    name = getattr(img, 'name', 'photo.jpg')
                    photos_data.append({"name": name, "content": encoded})
                except: continue
            new_sec['photos_base64'] = photos_data
        if 'photos' in new_sec: del new_sec['photos']
        sections_copy.append(new_sec)
    return sections_copy

def base64_to_images(sections_data):
    """Reconstruit les images à partir du JSON chargé."""
    for s in sections_data:
        if s.get('photos_base64'):
            restored_photos = []
            for p_data in s['photos_base64']:
                try:
                    img_bytes = base64.b64decode(p_data['content'])
                    buf = io.BytesIO(img_bytes)
                    buf.name = p_data['name']
                    restored_photos.append(buf)
                except: continue
            s['photos'] = restored_photos
    return sections_data

# --- FONCTION GÉNÉRATION PDF (CORRIGÉE : POLICE STANDARD) ---
def generate_pdf():
    class PDF(FPDF):
        def header(self):
            # En-tête optionnel ou Logo
            if os.path.exists("logo.png"):
                try: self.image("logo.png", 10, 8, 33)
                except: pass
            self.set_font('Arial', 'B', 15)
            # Décalage à droite pour le titre si logo
            self.cell(80) 
            self.ln(20)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Utilisation stricte de Arial/Helvetica pour éviter les crashs
    font_family = "Arial" 

    # TITRE ENCADRÉ
    pdf.set_fill_color(0, 51, 102) # Bleu foncé
    pdf.set_text_color(255, 255, 255) # Blanc
    pdf.set_font(font_family, 'B', 18)
    # encodage latin-1 pour gérer les accents français de base
    titre = "RAPPORT D'INTERVENTION TECHNIQUE"
    pdf.cell(0, 15, titre, ln=True, align='C', fill=True)
    
    # INFOS GÉNÉRALES
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_family, '', 11)
    pdf.ln(5)
    
    # Fonction helper pour nettoyer le texte (évite les erreurs d'encodage)
    def clean_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    pdf.cell(0, 7, f"Client : {clean_text(st.session_state.client_name)}", ln=True)
    pdf.cell(0, 7, f"Adresse : {clean_text(st.session_state.adresse)}", ln=True)
    date_str = st.session_state.date_visite.strftime('%d/%m/%Y') if st.session_state.date_visite else ""
    pdf.cell(0, 7, f"Date : {date_str} | Technicien : {clean_text(st.session_state.technicien)}", ln=True)
    pdf.ln(10)

    # PARTICIPANTS
    if st.session_state.participants:
        pdf.set_font(font_family, 'B', 12)
        pdf.set_fill_color(230, 230, 230) # Gris clair
        pdf.cell(0, 10, " PERSONNES PRESENTES", ln=True, fill=True)
        pdf.set_font(font_family, '', 10)
        for p in st.session_state.participants:
            nom = clean_text(p.get('nom', ''))
            tel = clean_text(p.get('tel', ''))
            email = clean_text(p.get('email', ''))
            pdf.cell(0, 8, f"- {nom} (Tel: {tel} | Email: {email})", ln=True)
        pdf.ln(10)

    # CORPS DU RAPPORT
    for idx, sec in enumerate(st.session_state.sections):
        titre = clean_text(sec.get('titre', 'Sans titre'))
        desc = clean_text(sec.get('description', ''))
        
        # Titre Section
        pdf.set_font(font_family, 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 10, titre.upper(), ln=True)
        # Ligne de soulignement
        pdf.set_draw_color(0, 51, 102)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        
        # Description
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_family, '', 11)
        pdf.multi_cell(0, 7, desc)
        pdf.ln(5)

        # Photos
        if sec.get('photos'):
            for i, img_file in enumerate(sec['photos']):
                try:
                    if hasattr(img_file, 'getvalue'):
                        img_data = img_file.getvalue()
                    else:
                        img_file.seek(0)
                        img_data = img_file.read()
                        
                    img = Image.open(io.BytesIO(img_data))
                    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                    
                    temp_path = f"temp_img_{idx}_{i}.jpg"
                    img.save(temp_path, "JPEG")
                    
                    if pdf.get_y() > 220: pdf.add_page()
                    
                    pdf.image(temp_path, w=100) # Largeur 10cm
                    pdf.ln(5)
                    os.remove(temp_path)
                except: continue
        pdf.ln(5)

    return pdf.output()

# --- FONCTION GÉNÉRATION WORD ---
def generate_word():
    doc = Document()
    doc.add_heading(f"RAPPORT : {st.session_state.client_name.upper()}", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    date_str = st.session_state.date_visite.strftime('%d/%m/%Y')
    p.add_run(f"Date : {date_str}\n").bold = True
    p.add_run(f"Technicien : {st.session_state.technicien}\n").bold = True
    p.add_run(f"Adresse : {st.session_state.adresse}")

    if st.session_state.participants:
        doc.add_heading("Participants", level=1)
        for p in st.session_state.participants:
            doc.add_paragraph(f"{p['nom']} - {p['tel']} - {p['email']}", style='List Bullet')

    doc.add_heading("Constats", level=1)
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    if hasattr(img_file, 'getvalue'):
                        d = img_file.getvalue()
                    else:
                        img_file.seek(0); d = img_file.read()
                    doc.add_picture(io.BytesIO(d), width=Inches(4.0))
                except: continue
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- SIDEBAR : SAUVEGARDE & RESTAURATION ---
st.sidebar.header("💾 Sauvegarde / Restauration")

# 1. Sauvegarder
save_data = {
    "client_name": st.session_state.client_name,
    "adresse": st.session_state.adresse,
    "technicien": st.session_state.technicien,
    "date_visite": str(st.session_state.date_visite),
    "participants": st.session_state.participants,
    "sections": images_to_base64(st.session_state.sections)
}
st.sidebar.download_button("📥 Sauvegarder JSON", json.dumps(save_data, indent=4), "sauvegarde.json")

# 2. Restaurer
uploaded_file = st.sidebar.file_uploader("📂 Charger JSON", type=["json"])
if uploaded_file and st.sidebar.button("♻️ RESTAURER"):
    try:
        data = json.load(uploaded_file)
        # Nettoyage des widgets
        for k in list(st.session_state.keys()):
            if k.startswith(('p_nom','p_tel','p_mail','sec_','cli_','adr_','tec_')):
                del st.session_state[k]

        st.session_state.client_name = data.get("client_name", "")
        st.session_state.adresse = data.get("adresse", "")
        st.session_state.technicien = data.get("technicien", "")
        try: st.session_state.date_visite = datetime.strptime(data.get("date_visite"), "%Y-%m-%d").date()
        except: st.session_state.date_visite = date.today()
        
        st.session_state.participants = data.get("participants", [])
        st.session_state.sections = base64_to_images(data.get("sections", []))
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erreur: {e}")

# --- INTERFACE ---
st.title("🏗️ Générateur de Rapport")

with st.expander("📌 Informations", expanded=True):
    c1, c2 = st.columns(2)
    st.session_state.client_name = c1.text_input("Client", value=st.session_state.client_name, key="cli_val")
    st.session_state.adresse = c1.text_input("Adresse", value=st.session_state.adresse, key="adr_val")
    st.session_state.date_visite = c2.date_input("Date", value=st.session_state.date_visite)
    st.session_state.technicien = c2.text_input("Technicien", value=st.session_state.technicien, key="tec_val")

st.header("👥 Participants")
if st.button("➕ Ajouter Participant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})
    st.rerun()

for i, p in enumerate(st.session_state.participants):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    p['nom'] = c1.text_input(f"Nom {i+1}", value=p.get('nom',''), key=f"p_nom_{i}")
    p['tel'] = c2.text_input(f"Tél {i+1}", value=p.get('tel',''), key=f"p_tel_{i}")
    p['email'] = c3.text_input(f"Email {i+1}", value=p.get('email',''), key=f"p_mail_{i}")
    if c4.button("🗑️", key=f"del_p_{i}"):
        st.session_state.participants.pop(i); st.rerun()

st.header("📝 Sections")
for idx, sec in enumerate(st.session_state.sections):
    with st.container():
        sec['titre'] = st.text_input(f"Titre Section {idx+1}", value=sec.get('titre',''), key=f"sec_titre_{idx}")
        sec['description'] = st.text_area(f"Détails Section {idx+1}", value=sec.get('description',''), key=f"sec_desc_{idx}")
        if sec.get('photos'): st.info(f"{len(sec['photos'])} photo(s)")
        
        new = st.file_uploader(f"Photos {idx+1}", accept_multiple_files=True, key=f"sec_img_{idx}")
        if new: sec['photos'] = new
        
        if st.button(f"🗑️ Supprimer Section {idx+1}", key=f"del_sec_{idx}"):
            st.session_state.sections.pop(idx); st.rerun()
        st.divider()

if st.button("➕ Ajouter Section"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []}); st.rerun()

st.header("🏁 Export")
c1, c2 = st.columns(2)
with c1:
    if st.button("📄 PDF"):
        res = generate_pdf()
        st.download_button("Télécharger PDF", bytes(res) if not isinstance(res, str) else res.encode('latin-1'), "rapport.pdf", "application/pdf")
with c2:
    if st.button("📝 Word"):
        st.download_button("Télécharger Word", generate_word().getvalue(), "rapport.docx")
