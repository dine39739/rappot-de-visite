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

# --- INITIALISATION DU SESSION STATE ---
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
                except:
                    continue
            new_sec['photos_base64'] = photos_data
        if 'photos' in new_sec:
            del new_sec['photos']
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
    client = st.session_state.get('client_name', 'SANS NOM')
    pdf.cell(0, 15, f"RAPPORT : {client.upper()}", ln=True, align='C')
    
    pdf.set_font("helvetica", '', 10)
    pdf.cell(0, 7, f"Client : {client}", ln=True)
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
                except:
                    continue
    return pdf.output()

# --- GÉNÉRATION WORD (CORRIGÉE) ---
def generate_word():
    doc = Document()
    client = st.session_state.get('client_name', 'SANS NOM')
    doc.add_heading(f"RAPPORT : {client}", 0)
    
    for s in st.session_state.sections:
        doc.add_heading(s.get('titre', 'Sans titre'), level=2)
        doc.add_paragraph(s.get('description', ''))
        
        if s.get('photos'):
            for img_file in s['photos']:
                try:
                    # Correction du bloc try/except qui causait l'erreur
                    image_stream = io.BytesIO(img_file.getvalue())
                    doc.add_picture(image_stream, width=Inches(3.5))
                except Exception:
                    continue
                    
    buffer = io.BytesIO()
    doc.save(buffer
