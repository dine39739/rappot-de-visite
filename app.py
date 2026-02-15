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
# On initialise les variables si elles n'existent pas
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
        # On sauvegarde les photos
        if s.get('photos'):
            photos_data = []
            for img in s['photos']:
                try:
                    # On lit le fichier, qu'il soit UploadedFile ou BytesIO
                    if hasattr(img, 'getvalue'):
                        img_bytes = img.getvalue()
                    else:
                        img_bytes = img.read()
                    
                    encoded = base64.b64encode(img_bytes).decode()
                    name = getattr(img, 'name', 'photo.jpg')
                    photos_data.append({"name": name, "content": encoded})
                except Exception as e:
                    print(f"Erreur encodage image: {e}")
                    continue
            new_sec['photos_base64'] = photos_data
        
        # On nettoie la clé 'photos' qui contient des objets non-sauvegardables en JSON
        if 'photos' in new_sec:
            del new_sec['photos']
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
                except Exception as e:
                    print(f"Erreur décodage image: {e}")
            s['photos'] = restored_photos
    return sections_data

# --- FONCTION GÉNÉRATION PDF (VOTRE MISE EN PAGE) ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Gestion Police (Fallback si DejaVu absent)
    font_family = "Helvetica" # Par défaut
    try:
        if os.path.exists("DejaVuSans.ttf"):
            pdf.add_font("DejaVu", '', 'DejaVuSans.ttf')
            font_family = "DejaVu"
    except:
        pass # On garde Helvetica si erreur

    # Logo
    if os.path.exists("logo.png"):
        try:
            pdf.image("logo.png", x=10, y=8, w=30)
        except: pass
    
    pdf.ln(20)

    # TITRE ENCADRÉ
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(font_family, 'B', 18) # 'B' pour Bold
    pdf.cell(0, 15, "RAPPORT D'INTERVENTION TECHNIQUE", ln=True, align='C', fill=True)
    
    # INFOS GÉNÉRALES
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_family, '', 11)
    pdf.ln(5)
    
    pdf.cell(0, 7, f"Client : {st.session_state.client_name}", ln=True)
    pdf.cell(0, 7, f"Adresse : {st.session_state.adresse}", ln=True)
    # Formatage de la date pour l'affichage
    date_str = st.session_state.date_visite.strftime('%d/%m/%Y') if st.session_state.date_visite else ""
    pdf.cell(0, 7, f"Date : {date_str} | Technicien : {st.session_state.technicien}", ln=True)
    pdf.ln(10)

    # PARTICIPANTS
    if st.session_state.participants:
        pdf.set_font(font_family, 'B', 12) # Gras
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 10, " PERSONNES PRÉSENTES", ln=True, fill=True)
        pdf.set_font(font_family, '', 10)
        for p in st.session_state.participants:
            nom = p.get('nom', '')
            tel = p.get('tel', '')
            email = p.get('email', '')
            pdf.cell(0, 8, f"- {nom} (Tél: {tel} | Email: {email})", ln=True)
        pdf.ln(10)

    # CORPS DU RAPPORT
    for idx, sec in enumerate(st.session_state.sections):
        titre = sec.get('titre', 'Sans titre')
        desc = sec.get('description', '')
        
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
                    # On crée un flux à partir des données de l'image
                    # .getvalue() si BytesIO, .read() si file uploadé frais, on gère les deux via BytesIO
                    if hasattr(img_file, 'getvalue'):
                        img_data = img_file.getvalue()
                    else:
                        img_file.seek(0)
                        img_data = img_file.read()
                        
                    img = Image.open(io.BytesIO(img_data))
                    
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    temp_path = f"temp_img_{idx}_{i}.jpg"
                    img.save(temp_path, "JPEG")
                    
                    if pdf.get_y() > 220:
                        pdf.add_page()
                    
                    # Largeur 90mm pour en mettre potentiellement 2 côte à côte ou centré
                    pdf.image(temp_path, w=100) 
                    pdf.ln(5)
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Erreur image PDF: {e}")
                    continue
        pdf.ln(5)

    return pdf.output()

# --- FONCTION GÉNÉRATION WORD ---
def generate_word():
    doc = Document()
    
    # Titre
    title = doc.add_heading(f"RAPPORT : {st.session_state.client_name.upper()}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Infos
    p = doc.add_paragraph()
    date_str = st.session_state.date_visite.strftime('%d/%m/%Y')
    p.add_run(f"Date de la visite : {date_str}\n").bold = True
    p.add_run(f"Technicien : {st.session_state.technicien}\n").bold = True
    p.add_run(f"Adresse : {st.session_state.adresse}")

    # Participants
    if st.session_state.participants:
        doc.add_heading("Participants", level=1)
        for p in st.session_state.participants:
            doc.add_paragraph(f"{p['nom']} - {p['tel']} - {p['email']}", style='List Bullet')

    # Sections
    doc.add_heading("Constats et Photos", level=1)
    
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    if hasattr(img_file, 'getvalue'):
                        img_data = img_file.getvalue()
                    else:
                        img_file.seek(0)
                        img_data = img_file.read()
                        
                    image_stream = io.BytesIO(img_data)
                    doc.add_picture(image_stream, width=Inches(4.0))
                    doc.add_paragraph() 
                except:
                    continue

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# BARRE LATÉRALE : SAUVEGARDE ET CHARGEMENT
# ==========================================
st.sidebar.header("💾 Sauvegarde & Restauration")

# 1. Création du dictionnaire de sauvegarde
data_to_save = {
    "client_name": st.session_state.client_name,
    "adresse": st.session_state.adresse,
    "technicien": st.session_state.technicien,
    # On convertit la date en string pour le JSON
    "date_visite": str(st.session_state.date_visite), 
    "participants": st.session_state.participants,
    # On convertit les sections et les images en base64
    "sections": images_to_base64(st.session_state.sections)
}

# 2. Bouton de téléchargement du JSON
st.sidebar.download_button(
    label="📥 Sauvegarder le dossier (.json)",
    data=json.dumps(data_to_save, indent=4),
    file_name=f"sauvegarde_{st.session_state.client_name or 'chantier'}.json",
    mime="application/json",
    help="Sauvegarde tout : textes, participants, date et PHOTOS."
)

st.sidebar.divider()

# 3. Chargement du JSON
uploaded_brouillon = st.sidebar.file_uploader("📂 Charger une sauvegarde", type=["json"])

if uploaded_brouillon and st.sidebar.button("♻️ RESTAURER LES DONNÉES"):
    try:
        data = json.load(uploaded_brouillon)
        
        # Nettoyage des clés de widgets pour forcer le rafraîchissement visuel
        for key in list(st.session_state.keys()):
            if key.startswith(('p_nom', 'p_tel', 'p_mail', 'sec_titre', 'sec_desc', 'cli_val', 'adr_val', 'tec_val')):
                del st.session_state[key]

        # Restauration des variables simples
        st.session_state.client_name = data.get("client_name", "")
        st.session_state.adresse = data.get("adresse", "")
        st.session_state.technicien = data.get("technicien", "")
        
        # Restauration de la date
        date_str = data.get("date_visite", str(date.today()))
        try:
            st.session_state.date_visite = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            st.session_state.date_visite = date.today()

        # Restauration des listes complexes
        st.session_state.participants = data.get("participants", [])
        
        # Restauration des sections et conversion Base64 -> Images
        st.session_state.sections = base64_to_images(data.get("sections", []))
        
        st.sidebar.success("✅ Données restaurées avec succès !")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Erreur lors de la lecture du fichier : {e}")

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================
st.title("🏗️ Générateur de Rapport Technique")

# --- BLOC 1 : INFOS GÉNÉRALES ---
with st.expander("📌 Informations du Chantier", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.client_name = st.text_input("Nom du Client / Projet", value=st.session_state.client_name, key="cli_val")
        st.session_state.adresse = st.text_input("Adresse de l'intervention", value=st.session_state.adresse, key="adr_val")
    with col2:
        st.session_state.date_visite = st.date_input("Date de la visite", value=st.session_state.date_visite)
        st.session_state.technicien = st.text_input("Technicien responsable", value=st.session_state.technicien, key="tec_val")

# --- BLOC 2 : PARTICIPANTS ---
st.header("👥 Participants")
if st.button("➕ Ajouter un participant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})
    st.rerun()

for i, p in enumerate(st.session_state.participants):
    with st.container():
        c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
        # On utilise value=p.get(...) pour que les données restaurées s'affichent
        p['nom'] = c1.text_input(f"Nom {i+1}", value=p.get('nom', ''), key=f"p_nom_{i}")
        p['tel'] = c2.text_input(f"Tél {i+1}", value=p.get('tel', ''), key=f"p_tel_{i}")
        p['email'] = c3.text_input(f"Email {i+1}", value=p.get('email', ''), key=f"p_mail_{i}")
        if c4.button("🗑️", key=f"del_p_{i}"):
            st.session_state.participants.pop(i)
            st.rerun()

# --- BLOC 3 : SECTIONS ET PHOTOS ---
st.header("📝 Corps du Rapport")

for idx, sec in enumerate(st.session_state.sections):
    with st.container():
        st.markdown(f"**Section {idx + 1}**")
        sec['titre'] = st.text_input("Titre", value=sec.get('titre', ''), key=f"sec_titre_{idx}", placeholder="ex: Toiture")
        sec['description'] = st.text_area("Observations", value=sec.get('description', ''), key=f"sec_desc_{idx}")
        
        # Affichage des photos déjà présentes (restaurées ou uploadées précédemment)
        if sec.get('photos'):
            st.info(f"📸 {len(sec['photos'])} photo(s) en mémoire pour cette section.")
            # Optionnel : Afficher les miniatures si besoin
            # st.image(sec['photos'], width=150)

        # Ajout de nouvelles photos
        new_photos = st.file_uploader(f"Ajouter des photos (Section {idx+1})", 
                                         accept_multiple_files=True, 
                                         type=['png', 'jpg', 'jpeg'], 
                                         key=f"sec_img_{idx}")
        
        # Si de nouvelles photos sont ajoutées, on les stocke
        # Note : st.file_uploader remplace la liste à chaque interaction s'il n'est pas vide.
        # Pour cumuler, il faudrait une logique plus complexe, ici on remplace ou on initialise.
        if new_photos:
            sec['photos'] = new_photos

        if st.button(f"🗑️ Supprimer la section {idx+1}", key=f"del_sec_{idx}"):
            st.session_state.sections.pop(idx)
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
        if not st.session_state.client_name:
            st.warning("Veuillez entrer un nom de client.")
        else:
            pdf_data = generate_pdf()
            # Conversion en bytes sécurisée pour streamlit
            if isinstance(pdf_data, str):
                pdf_bytes = pdf_data.encode('latin-1')
            else:
                pdf_bytes = bytes(pdf_data)
                
            st.download_button(
                label="⬇️ Télécharger le Rapport (PDF)",
                data=pdf_bytes,
                file_name=f"Rapport_{st.session_state.client_name}.pdf",
                mime="application/pdf"
            )

with c_word:
    if st.button("📝 Générer Word"):
        word_buffer = generate_word()
        st.download_button(
            label="⬇️ Télécharger le Rapport (Word)",
            data=word_buffer.getvalue(),
            file_name=f"Rapport_{st.session_state.client_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
