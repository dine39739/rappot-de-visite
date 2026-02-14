import streamlit as st
from datetime import date
from fpdf import FPDF
from PIL import Image
import os
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Tech-Report Pro", layout="wide", page_icon="🏗️")

# --- INITIALISATION DES VARIABLES (SESSION STATE) ---
if 'participants' not in st.session_state:
    st.session_state.participants = []
if 'sections' not in st.session_state:
    st.session_state.sections = [{'titre': '', 'description': '', 'photos': []}]

# --- STYLE CSS POUR LE RENDU ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .section-container { border: 1px solid #ddd; padding: 20px; border-radius: 10px; margin-bottom: 20px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Générateur de Rapport Technique")
st.info("Remplissez les sections ci-dessous. Vous pouvez ajouter autant de participants et de sections que nécessaire.")

# --- ÉTAPE 1 : INFOS GÉNÉRALES ---
with st.expander("📌 Informations du Chantier", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input("Nom du Client / Projet", placeholder="ex: Résidence Les Palmiers")
        adresse = st.text_input("Adresse de l'intervention")
    with col2:
        date_visite = st.date_input("Date de la visite", date.today())
        technicien = st.text_input("Technicien responsable")

# --- ÉTAPE 2 : PARTICIPANTS ---
st.header("👥 Participants")
if st.button("➕ Ajouter un participant"):
    st.session_state.participants.append({"nom": "", "tel": "", "email": ""})

for i, p in enumerate(st.session_state.participants):
    with st.container():
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
        sec['titre'] = st.text_input("Titre de la section", value=sec['titre'], key=f"sec_titre_{idx}", placeholder="ex: Constatations en toiture")
        sec['description'] = st.text_area("Observations détaillées", value=sec['description'], key=f"sec_desc_{idx}")
        
        # Gestion des photos pour cette section
        sec['photos'] = st.file_uploader(f"Ajouter des photos (Section {idx+1})", 
                                         accept_multiple_files=True, 
                                         type=['png', 'jpg', 'jpeg'], 
                                         key=f"sec_img_{idx}")
        
        if len(st.session_state.sections) > 1:
            if st.button(f"❌ Supprimer la section {idx+1}", key=f"del_sec_{idx}"):
                st.session_state.sections.pop(idx)
                st.rerun()
        st.divider()

if st.button("➕ Ajouter une Section de travail"):
    st.session_state.sections.append({'titre': '', 'description': '', 'photos': []})

# --- FONCTION DE GÉNÉRATION PDF ---
def generate_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

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
    pdf.set_font("helvetica", '', 18)
  
    # Cell(largeur, hauteur, texte, bordure, retour ligne, alignement, remplissage)
    pdf.cell(0, 15, "RAPPORT D'INTERVENTION TECHNIQUE", ln=True, align='C', fill=True)
    # Header
    
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 15, "RAPPORT D'INTERVENTION", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, f"Projet : {client_name}", ln=True, align='C')
    pdf.cell(0, 10, f"Date : {date_visite} | Technicien : {technicien}", ln=True, align='C')
    pdf.ln(10)

    # Participants
    if st.session_state.participants:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, " LISTE DES PERSONNES PRÉSENTES", ln=True, fill=True)
        pdf.set_font("helvetica", size=10)
        for p in st.session_state.participants:
            pdf.cell(0, 8, f"• {p['nom']} - Tel: {p['tel']} - Email: {p['email']}", ln=True)
        pdf.ln(10)

    # Contenu
    for sec in st.session_state.sections:
        if sec['titre']:
            pdf.set_font("helvetica", 'B', 14)
            pdf.set_text_color(0, 51, 102)
            pdf.cell(0, 10, sec['titre'].upper(), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", size=11)
            pdf.multi_cell(0, 7, sec['description'])
            pdf.ln(5)

            # Photos de la section
            if sec['photos']:
                for img_file in sec['photos']:
                    try:
                        img = Image.open(img_file)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        # Sauvegarde temporaire propre
                        temp_path = f"temp_img_{img_file.name}"
                        img.save(temp_path)
                        
                        # On vérifie la place restante sur la page
                        if pdf.get_y() > 200: 
                            pdf.add_page()
                            
                        pdf.image(temp_path, w=90) # Largeur 90mm
                        pdf.ln(5)
                        os.remove(temp_path)
                    except Exception as e:
                        st.error(f"Erreur image : {e}")
            pdf.ln(5)

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

# --- PROCHAINE ÉTAPE : GOOGLE DRIVE ---
# Note : Pour lier à Drive, il faudra configurer les "Secrets" dans Streamlit Cloud.
