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
# --- FONCTION DE GÉNÉRATION PDF ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- 1. CHARGEMENT DE LA POLICE UNICODE ---
    # Assurez-vous que le fichier .ttf est bien sur votre GitHub
    pdf.add_font("DejaVu", '', 'DejaVuSans.ttf')
    pdf.set_font("DejaVu", '', 12)

    # --- 2. EN-TÊTE AVEC LOGO ---
    # pdf.image(nom_du_fichier, x, y, largeur)
    # Si le fichier logo.png existe, on l'affiche
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=30)
    
    pdf.ln(20) # Saut de ligne après le logo

    # --- 3. TITRE ENCADRÉ (Bleu foncé, texte blanc) ---
    # Couleurs RGB : Bleu foncé (0, 51, 102), Blanc (255, 255, 255)
    pdf.set_fill_color(0, 51, 102)  # Couleur du fond de l'encadré
    pdf.set_text_color(255, 255, 255) # Couleur du texte
    pdf.set_font("DejaVu", '', 18)
    
    # Cell(largeur, hauteur, texte, bordure, retour ligne, alignement, remplissage)
    pdf.cell(0, 15, "RAPPORT D'INTERVENTION TECHNIQUE", ln=True, align='C', fill=True)
    
    # --- 4. RÉINITIALISATION POUR LE RESTE DU TEXTE ---
    pdf.set_text_color(0, 0, 0) # On repasse en noir
    pdf.set_font("DejaVu", '', 11)
    pdf.ln(5)
    
    # Infos générales (sous le titre)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"Client : {client_name}", ln=True)
    pdf.cell(0, 7, f"Adresse : {adresse}", ln=True)
    pdf.cell(0, 7, f"Date : {date_visite} | Technicien : {technicien}", ln=True)
    pdf.ln(10)

    # --- 5. SECTION PARTICIPANTS ---
    if st.session_state.participants:
        pdf.set_font("helvetica", '', 12)
        pdf.set_fill_color(230, 230, 230) # Gris très clair
        pdf.cell(0, 10, " PERSONNES PRÉSENTES", ln=True, fill=True)
        pdf.set_font("DejaVu", '', 10)
        for p in st.session_state.participants:
            pdf.cell(0, 8, f"• {p['nom']} (Tél: {p['tel']} | Email: {p['email']})", ln=True)
        pdf.ln(10)

    # --- 6. CORPS DU RAPPORT ---
    for sec in st.session_state.sections:
        if sec['titre']:
            # Titre de section stylisé (souligné bleu)
            pdf.set_font("helvetica", '', 14)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 10, sec['titre'].upper(), ln=True)
            pdf.set_draw_color(0, 51, 102)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(2)
            
            # Description
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", '', 11)
            pdf.multi_cell(0, 7, sec['description'])
            pdf.ln(5)

            # Photos
            if sec['photos']:
                # On organise les photos par 2 par ligne pour gagner de la place
                col_width = 90
                for i, img_file in enumerate(sec['photos']):
                    try:
                        img = Image.open(img_file)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        temp_path = f"temp_{idx}_{i}_{img_file.name}"
                        img.save(temp_path)
                        
                        # Gestion de l'espace pour ne pas couper l'image en bas de page
                        if pdf.get_y() > 220:
                            pdf.add_page()
                        
                        pdf.image(temp_path, w=col_width)
                        pdf.ln(5)
                        os.remove(temp_path)
                    except Exception as e:
                        st.error(f"Erreur photo : {e}")
            pdf.ln(10)

    return pdf.output()

# --- BOUTON FINAL ---
st.divider()
if st.button("🚀 GÉNÉRER LE RAPPORT PDF"):
    if not client_name or not technicien:
        st.warning("Veuillez remplir au moins le nom du client et du technicien.")
    else:
        with st.spinner("Création du PDF en cours..."):
            pdf_data = generate_pdf()
            st.success("✅ Votre rapport est prêt !")
            st.download_button(
                label="⬇️ Télécharger le Rapport (PDF)",
                data=bytes(pdf_data),
                file_name=f"Rapport_{client_name}_{date_visite}.pdf",
                mime="application/pdf"
            )


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
