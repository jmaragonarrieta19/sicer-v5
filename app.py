import streamlit as st
import pandas as pd
from datetime import datetime
import math
from fpdf import FPDF
import google.generativeai as genai
from PIL import Image
import os
import re
import base64
import time
import uuid
import json
import qrcode
import firebase_admin
from firebase_admin import credentials, db
import io
from pypdf import PdfReader, PdfWriter

# ==========================================
# 1. DIRECTORIOS Y CONFIGURACIÓN IA
# ==========================================
os.makedirs("solicitudes_img", exist_ok=True) 
os.makedirs("certificados_emitidos", exist_ok=True) 

# ==========================================
# 2. CLASE PDF PERSONALIZADA
# ==========================================
class CustomPDF(FPDF):
    def rotate(self, angle, x, y):
        angle = angle * math.pi / 180
        c = math.cos(angle)
        s = math.sin(angle)
        cx = x * self.k
        cy = (self.h - y) * self.k
        self._out(f'q {c:.5f} {s:.5f} {-s:.5f} {c:.5f} {cx:.2f} {cy:.2f} cm 1 0 0 1 {-cx:.2f} {-cy:.2f} cm')

    def stop_transform(self):
        self._out('Q')

# ==========================================
# 3. ICONOGRAFÍA MODERNA
# ==========================================
ICON_AI = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c.132 5.4 4.6 9.868 10 10-5.4.132-9.868 4.6-10 10-0.132-5.4-4.6-9.868-10-10 5.4-0.132 9.868-4.6 10-10Z"/></svg>'
ICON_DOC = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M8 13h6"/><path d="M8 17h8"/></svg>'
ICON_BUILDING = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"/><path d="M9 7h6"/><path d="M9 11h6"/><path d="M9 15h6"/></svg>'
ICON_IMAGE = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>'
ICON_TYPE = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>'
ICON_USERS = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
ICON_HISTORY = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
ICON_SETTINGS = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>'

def section_header(icon, title):
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 14px; margin-top: 15px; margin-bottom: 25px; padding-bottom: 12px; border-bottom: 1px solid #E2E8F0;">
            {icon}
            <h2 style="margin: 0; font-size: 1.45rem; color: #1E293B; font-weight: 700; letter-spacing: -0.5px;">{title}</h2>
        </div>
    """, unsafe_allow_html=True)

def get_download_icon(ruta):
    with open(ruta, "rb") as f:
        b64_pdf = base64.b64encode(f.read()).decode('utf-8')
    file_n = os.path.basename(ruta)
    return f'''
    <a href="data:application/pdf;base64,{b64_pdf}" download="{file_n}" title="Descargar Certificado"
       style="display: inline-flex; align-items: center; justify-content: center; background-color: #10B981; color: white; width: 38px; height: 38px; border-radius: 8px; text-decoration: none; transition: all 0.2s; box-shadow: 0 2px 4px rgba(16,185,129,0.3);">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
    </a>
    '''

# ==========================================
# 4. CONFIGURACIÓN DE PÁGINA Y DISEÑO URBANO
# ==========================================
st.set_page_config(page_title="SICER IA v9.1", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    p, h1, h2, h3, h4, h5, h6, li, .stTextInput input, .stTextArea textarea, .stSelectbox div { 
        font-family: 'Inter', sans-serif !important; 
    }
    
    .stApp { background-color: #F8F9FA !important; } 
    header {display: none !important;} footer {display: none !important;}
    
    .block-container { 
        padding-top: 80px !important; 
        padding-bottom: 5rem !important; 
        max-width: 1150px; 
    }
    
    .top-navbar-bg {
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 60px;
        background-color: #4E008E;
        z-index: 99999;
    }
    .navbar-logo {
        position: fixed;
        top: 13px; left: 40px;
        color: white;
        font-size: 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-style: italic;
        letter-spacing: -0.5px;
        z-index: 100000;
        display: flex;
        align-items: center;
    }
    .navbar-logo span {
        font-size: 0.8rem;
        font-weight: 600;
        font-style: normal;
        background: rgba(255,255,255,0.2);
        padding: 3px 8px;
        border-radius: 99px;
        margin-left: 10px;
    }
    
    span.logout-anchor { display: none; }
    div[data-testid="stElementContainer"]:has(.logout-anchor) + div[data-testid="stElementContainer"] {
        position: fixed;
        top: 10px;
        right: 40px;
        z-index: 100000;
        width: auto !important;
    }
    div[data-testid="stElementContainer"]:has(.logout-anchor) + div[data-testid="stElementContainer"] button {
        background-color: transparent !important; 
        color: #ffffff !important;
        border: 1.5px solid rgba(255,255,255,0.6) !important; 
        border-radius: 999px !important;
        padding: 0.3rem 1.2rem !important; 
        font-weight: 600 !important; 
        font-size: 0.85rem !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stElementContainer"]:has(.logout-anchor) + div[data-testid="stElementContainer"] button p { 
        color: #ffffff !important; 
        margin: 0 !important;
        white-space: nowrap !important;
    }
    div[data-testid="stElementContainer"]:has(.logout-anchor) + div[data-testid="stElementContainer"] button:hover { 
        background-color: #ffffff !important; 
        border-color: #ffffff !important;
    }
    div[data-testid="stElementContainer"]:has(.logout-anchor) + div[data-testid="stElementContainer"] button:hover p { 
        color: #4E008E !important; 
    }

    div[data-testid="stTabs"] {
        margin-top: 1rem;
    }
    div[data-testid="stTabs"] > div:nth-child(1) {
        position: sticky !important;
        top: 60px !important;
        z-index: 99990 !important;
        background-color: #F8F9FA !important;
        padding: 10px 0 0 0 !important;
        border-bottom: 2px solid #E2E8F0 !important;
        margin-bottom: 2.5rem !important;
    }
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 40px !important; 
        padding-bottom: 0px !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        display: flex !important;
        justify-content: center !important; 
        width: 100% !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 10px 4px 14px 4px !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #64748B !important;
        transition: color 0.3s ease !important;
        white-space: nowrap !important;
        min-width: max-content !important; 
    }
    div[data-testid="stTabs"] button[role="tab"] p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover {
        color: #4E008E !important;
        background-color: transparent !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #4E008E !important;
        border-bottom: 3px solid #4E008E !important; 
        background-color: transparent !important;
        box-shadow: none !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #4E008E !important;
        font-weight: 800 !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"], 
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none !important;
    }

    .purple-banner {
        background-color: #F3E8FF; 
        color: #4E008E;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-weight: 700;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 12px;
        border-left: 6px solid #4E008E;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important; 
        border-radius: 16px !important;
        border: 1px solid #E2E8F0 !important; 
        padding: 2.5rem !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
        margin-bottom: 2rem !important;
    }
    
    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }
    
    .stTextInput label p, .stTextArea label p, .stSelectbox label p, .stFileUploader label p, .stMultiSelect label p, .stDateInput label p { 
        color: #4E008E !important; 
        font-weight: 700 !important; 
        font-size: 0.85rem !important; 
        margin-bottom: 6px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div, .stDateInput div {
        border-radius: 12px !important; 
        border: 1px solid #CBD5E1 !important;
        padding: 0.7rem 1rem !important; 
        font-size: 0.95rem !important;
        background-color: #F8F9FA !important; 
        color: #1E293B !important; 
        transition: all 0.2s ease !important;
    }
    .stTextInput input:disabled, .stTextArea textarea:disabled {
        background-color: #F1F5F9 !important;
        color: #64748B !important;
        border: 1px dashed #CBD5E1 !important;
        cursor: not-allowed !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within, .stMultiSelect div[data-baseweb="select"] > div:focus-within, .stDateInput div:focus-within { 
        border-color: #4E008E !important; 
        box-shadow: 0 0 0 3px rgba(78, 0, 142, 0.15) !important; 
        background-color: #ffffff !important;
    }
    
    button[kind="primary"], 
    .stButton > button[kind="primary"], 
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #4E008E 0%, #6A0DAD 100%) !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 999px !important; 
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important; 
        min-height: 42px !important;
    }
    button[kind="primary"] *, 
    div[data-testid="stFormSubmitButton"] > button * {
        color: #ffffff !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }
    button[kind="primary"]:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover {
        box-shadow: 0 6px 20px rgba(78, 0, 142, 0.4) !important;
        transform: translateY(-2px);
    }
    
    button[kind="secondary"], .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        border: 2px solid #4E008E !important;
        color: #4E008E !important;
        border-radius: 999px !important; 
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        width: 100% !important;
        min-height: 42px !important;
        transition: all 0.3s ease !important;
    }
    button[kind="secondary"] * { 
        color: #4E008E !important; 
        margin: 0 !important; 
        white-space: nowrap !important;
    }
    button[kind="secondary"]:hover { 
        background-color: #4E008E !important; 
        border-color: #4E008E !important;
    }
    button[kind="secondary"]:hover * { 
        color: #ffffff !important; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. MOTOR HÍBRIDO SEGURO (SECRETOS + NUBE)
# ==========================================
ARCHIVO_CONFIG = "config_sicer.json"
ARCHIVO_HISTORIAL = "historial_sicer.json"

URL_FIREBASE = "https://sicer-ia-core-default-rtdb.firebaseio.com/" 
RUTA_LLAVE_FIREBASE = "firebase_key.json" 

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred, {'databaseURL': URL_FIREBASE})
                return True
            elif os.path.exists(RUTA_LLAVE_FIREBASE):
                cred = credentials.Certificate(RUTA_LLAVE_FIREBASE)
                firebase_admin.initialize_app(cred, {'databaseURL': URL_FIREBASE})
                return True
            else:
                return False
        except Exception:
            return False
    return True

def cargar_configuracion():
    datos_nube = None
    if init_firebase():
        try:
            ref = db.reference('config_db')
            datos_nube = ref.get()
        except Exception:
            pass
            
    if datos_nube:
        try:
            with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
                json.dump(datos_nube, f, ensure_ascii=False, indent=4)
        except Exception: pass
        return datos_nube
        
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
        
    return {
        "usuarios": {
            "admin": {"clave": "admin123", "rol": "administrador"}
        },
        "empresas": [{"nombre": "ACEROSNOR S.A.C.", "ruc": "20600000000", "direccion": "Jaén, Cajamarca"}],
        "propiedades_dinamicas": [
            {"id": str(uuid.uuid4()), "label": "Material", "default": "ACERO ZINCALUM ALUZINC", "current": "ACERO ZINCALUM ALUZINC"},
            {"id": str(uuid.uuid4()), "label": "Norma", "default": "ASTM A792", "current": "ASTM A792"}
        ],
        "lista_carac": ["Peso liviano", "Máxima resistencia", "Resistencia a la corrosión y flexión"],
        "mensaje_intro": "GARANTIZA LA FABRICACIÓN DE COBERTURAS DE ALUZINC DE ACUERDO A LAS CARACTERÍSTICAS SOLICITADAS POR {cliente} {tipo_doc} {num_doc} (SEGÚN {comprobante}), POR LO QUE CERTIFICA LA CALIDAD DEL PRODUCTO TERMINADO CON LAS SIGUIENTES CARACTERÍSTICAS TÉCNICAS:",
        "fuente_intro": "Arial", "tamano_intro": 10, "align_intro": "J", "linea_intro": 5,
        "caracteristicas_18": "- Peso liviano\n- Máxima resistencia\n- Resistencia a la corrosión y flexión",
        "mensaje_final": "En {empresa} por sus años de experiencia y trayectoria en el mercado, le ofrece procesos de manufactura, personal técnico calificado y maquinaria de ultima generación que garantizan la máxima calidad de nuestro producto terminado.",
        "fuente_final": "Arial", "tamano_final": 10, "align_final": "J", "linea_final": 5,
        "solicitudes": [],
        "api_key": "",
        "model_name": "models/gemini-3.1-flash-lite-preview",
        "titulo_adicional": "PROTECCIÓN ADICIONAL",
        "texto_adicional": "En la cara principal posee una capa de film de PVC termo aplicado, que tiene como finalidad mantener intacta la pintura al momento en el proceso de conformado, manipulación e instalación.",
        "firmas_config": {}
    }

def guardar_configuracion(datos):
    try:
        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception: pass
    
    if init_firebase():
        try:
            ref = db.reference('config_db')
            ref.set(datos)
        except Exception: pass

def cargar_historial():
    datos_nube = None
    if init_firebase():
        try:
            ref = db.reference('historial_db')
            datos_nube = ref.get()
        except Exception: pass
        
    if datos_nube:
        try:
            with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
                json.dump(datos_nube, f, ensure_ascii=False, indent=4)
        except Exception: pass
        return datos_nube
        
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return []

def guardar_historial(datos):
    try:
        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception: pass
    
    if init_firebase():
        try:
            ref = db.reference('historial_db')
            ref.set(datos)
        except Exception: pass

# ==========================================
# 6. CARGA AL ESTADO DE LA SESIÓN
# ==========================================
if 'config_db' not in st.session_state: st.session_state.config_db = cargar_configuracion()
if 'historial_db' not in st.session_state: st.session_state.historial_db = cargar_historial()

if "empresas" in st.session_state.config_db and len(st.session_state.config_db["empresas"]) > 0:
    if isinstance(st.session_state.config_db["empresas"][0], str):
        st.session_state.config_db["empresas"] = [{"nombre": e, "ruc": "", "direccion": "Jaén"} for e in st.session_state.config_db["empresas"]]

todas_empresas_nombres = [e["nombre"] for e in st.session_state.config_db.get("empresas", [])]
for u_name, u_data in st.session_state.config_db.get("usuarios", {}).items():
    if "empresas_permitidas" not in u_data and u_data.get("rol") != "cliente":
        st.session_state.config_db["usuarios"][u_name]["empresas_permitidas"] = todas_empresas_nombres

for key in ["usuarios", "empresas", "propiedades_dinamicas", "lista_carac", "mensaje_intro", "fuente_intro", "tamano_intro", "align_intro", "linea_intro", "caracteristicas_18", "mensaje_final", "fuente_final", "tamano_final", "align_final", "linea_final", "solicitudes", "api_key", "model_name", "titulo_adicional", "texto_adicional", "firmas_config"]:
    if key not in st.session_state: 
        default_val = [] if key in ["solicitudes", "empresas", "propiedades_dinamicas", "lista_carac"] else ({} if key == "firmas_config" else "")
        val = st.session_state.config_db.get(key, default_val)
        if key == "solicitudes" and not isinstance(val, list): val = []
        st.session_state[key] = val

if not isinstance(st.session_state.solicitudes, list): st.session_state.solicitudes = []

if 'logueado' not in st.session_state: st.session_state.logueado = False
if 'usuario_actual' not in st.session_state: st.session_state.usuario_actual = ""
if 'rol' not in st.session_state: st.session_state.rol = ""
if 'fuentes_custom' not in st.session_state: st.session_state.fuentes_custom = []
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'ia_procesado' not in st.session_state: st.session_state.ia_procesado = False
if 'show_download' not in st.session_state: st.session_state.show_download = False
if 'ultimo_pdf_ruta' not in st.session_state: st.session_state.ultimo_pdf_ruta = None
if 'modo_vista' not in st.session_state: st.session_state.modo_vista = 'login'

if 'datos_form' not in st.session_state:
    st.session_state.datos_form = {"empresa": "", "ruc_emisor": "", "cliente": "", "ruc": "", "comprobante": "", "vendedor": "", "ciudad": "Jaén", "cantidad": "", "incluir_proteccion": True}

def limpiar_nombre(nombre): return re.sub(r'[^a-zA-Z0-9]', '', str(nombre)).upper()
def obtener_ruta_logo(n): return os.path.join(os.getcwd(), f"logo_{limpiar_nombre(n)}.png")
def obtener_ruta_fuente(n): return os.path.join(os.getcwd(), f"fuente_{limpiar_nombre(n)}.ttf")
def obtener_ruta_firma_legacy(n): return os.path.join(os.getcwd(), f"firma_{limpiar_nombre(n)}.png")
def obtener_ruta_plantilla(n): return os.path.join(os.getcwd(), f"plantilla_{limpiar_nombre(n)}.pdf")

def obtener_imagen_html(ruta_imagen, altura_px=100):
    with open(ruta_imagen, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    return f'<div style="height: {altura_px}px; width: 100%; display: flex; align-items: center; justify-content: center; margin-bottom: 15px;"><img src="data:image/png;base64,{encoded_string}" style="max-height: 100%; max-width: 100%; object-fit: contain;"></div>'

def limpiar_formulario_emision():
    st.session_state.datos_form = {"empresa": "", "ruc_emisor": "", "cliente": "", "ruc": "", "comprobante": "", "vendedor": "", "ciudad": "Jaén", "cantidad": "", "incluir_proteccion": True}
    st.session_state.ia_procesado = False
    st.session_state.uploader_key += 1

def es_comprobante_valido(comprobante):
    patron = r'^[FBE][A-Z0-9]{3}-\d+$'
    return bool(re.match(patron, comprobante.strip().upper()))

# ==========================================
# 7. MODALES DE SEGURIDAD Y RECHAZOS
# ==========================================
@st.dialog("🔓 Verificación de seguridad")
def modal_verificar_clave(user_objetivo):
    st.write(f"Ingrese su clave de administrador para ver la contraseña de **{user_objetivo}**:")
    pass_input = st.text_input("Clave de administrador", type="password", key="modal_pass_input")
    st.write("")
    col_m1, col_m2 = st.columns(2)
    if col_m1.button("Confirmar", type="primary", use_container_width=True):
        admin_actual = st.session_state.usuario_actual
        if st.session_state.usuarios[admin_actual]["clave"] == pass_input:
            st.success(f"Contraseña de '{user_objetivo}': **{st.session_state.usuarios[user_objetivo]['clave']}**")
            time.sleep(2)
            st.rerun()
        else: st.error("❌ Clave incorrecta.")
    if col_m2.button("Cancelar", use_container_width=True): st.rerun()

@st.dialog("⚠️ Confirmar eliminación")
def modal_confirmar_eliminacion(usuario_a_borrar):
    st.warning(f"¿Estás seguro que deseas eliminar permanentemente al usuario **{usuario_a_borrar}**?")
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Sí, eliminar", type="primary", use_container_width=True):
        del st.session_state.usuarios[usuario_a_borrar]
        st.session_state.config_db["usuarios"] = st.session_state.usuarios
        guardar_configuracion(st.session_state.config_db)
        st.success(f"Usuario {usuario_a_borrar} eliminado con éxito.")
        time.sleep(1.5)
        st.rerun()
    if c2.button("Cancelar", use_container_width=True): st.rerun()

@st.dialog("🚫 Rechazar Solicitud")
def modal_rechazar_solicitud(solicitud_id, comp_leido=""):
    motivo = st.text_area("Indique el motivo del rechazo:", placeholder="Ej. Imagen borrosa, RUC inválido, comprobante duplicado...")
    st.write("")
    c1, c2 = st.columns(2)
    if c1.button("Confirmar Rechazo", type="primary", use_container_width=True):
        if not motivo.strip():
            st.error("⚠️ Debe ingresar un motivo.")
        else:
            for idx, sol in enumerate(st.session_state.solicitudes):
                if sol['id'] == solicitud_id:
                    st.session_state.solicitudes[idx]['estado'] = 'Rechazado'
                    st.session_state.solicitudes[idx]['motivo_rechazo'] = motivo.strip()
                    if comp_leido.strip():
                        st.session_state.solicitudes[idx]['comprobante'] = comp_leido.strip().upper()
                    elif st.session_state.solicitudes[idx].get('comprobante', '') in ['Por escanear', '']:
                        st.session_state.solicitudes[idx]['comprobante'] = 'S/N'
                    if os.path.exists(sol.get('ruta_imagen', '')):
                        try: os.remove(sol['ruta_imagen'])
                        except: pass
            st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
            guardar_configuracion(st.session_state.config_db)
            limpiar_formulario_emision()
            st.success("✅ Solicitud rechazada y notificada al vendedor.")
            time.sleep(1.5)
            st.rerun()
    if c2.button("Cancelar", use_container_width=True): st.rerun()

@st.dialog("⚠️ Alerta de Seguridad")
def modal_alerta_ruc(solicitud_id, comp_leido):
    st.markdown("""
        <div style='background-color:#FEF2F2; border-left: 6px solid #DC2626; padding: 20px; border-radius: 8px; margin-bottom: 20px;'>
            <h3 style='color:#B91C1C; margin-top:0; font-size: 1.1rem;'>🚫 COMPROBANTE NO VÁLIDO</h3>
            <p style='color:#7F1D1D; font-size:0.9rem; margin-bottom:0;'>El documento escaneado no es válido o la empresa no se encuentra registrada en el catálogo del sistema. La emisión ha sido bloqueada por seguridad.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if solicitud_id:
        st.markdown("<p style='font-weight:600; font-size:0.9rem; color:#1E293B;'>Puede rechazar automáticamente esta solicitud para que el vendedor sea notificado:</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("Rechazar Comprobante", type="primary", use_container_width=True):
            for idx, sol in enumerate(st.session_state.solicitudes):
                if sol['id'] == solicitud_id:
                    st.session_state.solicitudes[idx]['estado'] = 'Rechazado'
                    st.session_state.solicitudes[idx]['motivo_rechazo'] = "Documento rechazado: Comprobante no válido o empresa no autorizada."
                    if comp_leido.strip():
                        st.session_state.solicitudes[idx]['comprobante'] = comp_leido.strip().upper()
                    elif st.session_state.solicitudes[idx].get('comprobante', '') in ['Por escanear', '']:
                        st.session_state.solicitudes[idx]['comprobante'] = 'S/N'
                    if os.path.exists(sol.get('ruta_imagen', '')):
                        try: os.remove(sol['ruta_imagen'])
                        except: pass
            st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
            guardar_configuracion(st.session_state.config_db)
            limpiar_formulario_emision()
            st.success("✅ Solicitud rechazada correctamente.")
            time.sleep(1.5)
            st.rerun()
        if c2.button("Cerrar", use_container_width=True): st.rerun()
    else:
        if st.button("Entendido", type="primary", use_container_width=True): st.rerun()

# ==========================================
# 8. FUNCIÓN PDF SEGURA 
# ==========================================
def render_texto_seguro(pdf, texto, align_code, font_name, font_size, line_height=5):
    pdf.set_font(font_name, '', font_size)
    texto_limpio = str(texto).replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<br>', '\n')
    pdf.multi_cell(0, line_height, texto_limpio, align=align_code)

def generar_pdf(empresa_emisora, ruc_emisor, cliente, ruc, comprobante, vendedor, ciudad, props_dinamicas, cantidad, carac_18, msg_final, num_cert, incluir_proteccion, texto_proteccion):
    pdf = CustomPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)
    
    fuentes_agregadas = [] 
    ruta_plantilla = obtener_ruta_plantilla(empresa_emisora)
    usar_plantilla = os.path.exists(ruta_plantilla)

    pdf.set_font("Arial", 'B', 28)
    pdf.set_text_color(225, 225, 225) 
    marca_agua = f"CERTIFICADO {num_cert}"
    posiciones = [(20, 80), (120, 80), (20, 160), (120, 160), (20, 240), (120, 240)]
    for x_pos, y_pos in posiciones:
        pdf.rotate(35, x_pos, y_pos)
        pdf.text(x=x_pos, y=y_pos, txt=marca_agua)
        pdf.stop_transform()
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_xy(10, 15)
    
    ruta_logo = obtener_ruta_logo(empresa_emisora)
    if os.path.exists(ruta_logo): 
        pdf.image(ruta_logo, x=10, y=10, h=18) 
    
    qr_data = f"CERT: {num_cert} | COMP: {comprobante} | RUC: {ruc_emisor}"
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    qr_temp_id = uuid.uuid4().hex
    qr_path = f"temp_qr_{qr_temp_id}.jpg" 
    
    try:
        img_qr.save(qr_path, format="JPEG", quality=90)
        pdf.image(qr_path, x=175, y=12, w=28) 
        
        pdf.set_font("Arial", 'B', 15)
        
        if os.path.exists(ruta_logo): 
            pdf.ln(12)
        else:
            pdf.ln(25)
            
        if not usar_plantilla:
            pdf.cell(0, 6, empresa_emisora, ln=True, align='C')
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 6, f"RUC: {ruc_emisor}", ln=True, align='C')
            pdf.ln(6)
        else:
            pdf.ln(10)
            
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 6, "CERTIFICADO DE CALIDAD", ln=True, align='C')
        pdf.ln(6)
        
        numero_limpio = str(ruc).strip()
        tipo_documento = "DNI" if len(numero_limpio) == 8 else "RUC"
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "OTORGADO A:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"{cliente}", ln=True)
        pdf.cell(0, 5, f"{tipo_documento}: {numero_limpio}", ln=True)
        pdf.ln(4)
        
        if st.session_state.fuente_intro not in ["Arial", "Times", "Courier"]:
            if st.session_state.fuente_intro not in fuentes_agregadas:
                try: 
                    pdf.add_font(st.session_state.fuente_intro, '', obtener_ruta_fuente(st.session_state.fuente_intro), uni=True)
                    fuentes_agregadas.append(st.session_state.fuente_intro)
                except: pass 
        
        texto_intro_formateado = st.session_state.mensaje_intro.format(cliente=cliente, tipo_doc=tipo_documento, num_doc=numero_limpio, comprobante=comprobante)
        texto_intro_completo = f"{empresa_emisora} CON RUC {ruc_emisor}, {texto_intro_formateado}"
        render_texto_seguro(pdf, texto_intro_completo, st.session_state.align_intro, st.session_state.fuente_intro, st.session_state.tamano_intro)
        pdf.ln(4)
        
        idx_num = 1
        for p in props_dinamicas:
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(35, 6, f"1.{idx_num} {p['label'].upper()}:")
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 6, p['default'].upper(), ln=True)
            idx_num += 1
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(35, 6, f"1.{idx_num} CANTIDAD:")
        pdf.set_font("Arial", '', 9)
        render_texto_seguro(pdf, cantidad, "L", "Arial", 9)
        pdf.ln(2)
        idx_num += 1
        
        pdf.set_font("Arial", 'B', 9)
        pdf.cell(0, 6, f"1.{idx_num} CARACTERÍSTICAS", ln=True)
        render_texto_seguro(pdf, carac_18, "L", "Arial", 9)
        pdf.ln(4)
        idx_num += 1
        
        titulo_add = st.session_state.config_db.get("titulo_adicional", "PROTECCIÓN ADICIONAL").strip()
        
        if incluir_proteccion and texto_proteccion and texto_proteccion.strip() != "":
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 6, f"1.{idx_num} {titulo_add.upper()}", ln=True)
            render_texto_seguro(pdf, texto_proteccion, "J", "Arial", 9)
            pdf.ln(4)
            idx_num += 1
        
        if st.session_state.fuente_final not in ["Arial", "Times", "Courier"]:
            if st.session_state.fuente_final not in fuentes_agregadas:
                try: 
                    pdf.add_font(st.session_state.fuente_final, '', obtener_ruta_fuente(st.session_state.fuente_final), uni=True)
                    fuentes_agregadas.append(st.session_state.fuente_final)
                except: pass
        
        texto_final_formateado = msg_final.format(empresa=empresa_emisora)
        render_texto_seguro(pdf, texto_final_formateado, st.session_state.align_final, st.session_state.fuente_final, st.session_state.tamano_final)
        pdf.ln(8) 
        
        firmas_activas = st.session_state.config_db.get("firmas_config", {}).get(empresa_emisora, [])
        legacy_firma = obtener_ruta_firma_legacy(empresa_emisora)

        if firmas_activas:
            pdf.ln(10)
            y_firma = pdf.get_y()
            num_firmas = len(firmas_activas)
            w_page = 210
            w_sig = w_page / num_firmas
            img_w = 35 
            
            for i, f_data in enumerate(firmas_activas):
                f_path = os.path.join(os.getcwd(), f"firma_{limpiar_nombre(empresa_emisora)}_{f_data['id']}.png")
                if os.path.exists(f_path):
                    center_x = (i * w_sig) + (w_sig / 2)
                    pdf.image(f_path, x=center_x - (img_w / 2), y=y_firma, w=img_w)
            
            pdf.set_y(y_firma + 22)
            pdf.set_font("Arial", 'B', 9)
            for i, f_data in enumerate(firmas_activas):
                pdf.set_xy(i * w_sig, y_firma + 22)
                pdf.cell(w_sig, 5, f_data['cargo'].upper(), align='C')
            pdf.ln(10)
            
        elif os.path.exists(legacy_firma):
            pdf.image(legacy_firma, x=(pdf.w - 35) / 2, y=pdf.get_y(), w=35)
            pdf.ln(20)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(0, 5, "GERENCIA", ln=True, align='C')
        else:
            pdf.ln(15) 
            
        pdf.set_font("Arial", 'I', 8)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ciudad_final_pdf = ciudad if ciudad and str(ciudad).strip() != "" else "Jaén"
        pdf.cell(0, 6, f"{ciudad_final_pdf} - Certificado {num_cert} - Fecha: {fecha_actual}", ln=True, align='R')
        
        # ---------------------------------------------------------
        # COMPATIBILIDAD ABSOLUTA DE BYTES (FPDF1 y FPDF2)
        # ---------------------------------------------------------
        res = pdf.output(dest='S')
        if isinstance(res, str):
            pdf_bytes = res.encode('latin-1', 'ignore')
        else:
            pdf_bytes = bytes(res)
            
        if usar_plantilla:
            try:
                template_reader = PdfReader(ruta_plantilla)
                overlay_reader = PdfReader(io.BytesIO(pdf_bytes))
                writer = PdfWriter()
                
                template_page = template_reader.pages[0]
                overlay_page = overlay_reader.pages[0]
                template_page.merge_page(overlay_page)
                writer.add_page(template_page)
                
                output_stream = io.BytesIO()
                writer.write(output_stream)
                pdf_bytes = output_stream.getvalue()
            except Exception as e:
                st.error(f"Error al aplicar la plantilla PDF: {e}")
                
    finally:
        if os.path.exists(qr_path):
            os.remove(qr_path)
            
    return pdf_bytes

# ==========================================
# 9. MÓDULOS DE PESTAÑAS (APP)
# ==========================================

def tab_emision():
    section_header(ICON_AI, "Escaneo inteligente automatizado")
    
    if st.session_state.rol == "administrador":
        empresas_permitidas_ui = [e["nombre"] for e in st.session_state.empresas]
    else:
        empresas_permitidas_ui = st.session_state.usuarios.get(st.session_state.usuario_actual, {}).get("empresas_permitidas", [])
        
    solicitudes_pendientes = [s for s in st.session_state.solicitudes if s['estado'] == 'Pendiente' and (st.session_state.rol == 'administrador' or s.get('empresa_destino') is None or s.get('empresa_destino') in empresas_permitidas_ui)]
    solicitud_seleccionada = None
    
    if solicitudes_pendientes:
        with st.expander(f"📥 Tienes {len(solicitudes_pendientes)} solicitudes pendientes", expanded=True):
            opciones = ["Seleccione una solicitud..."] + [f"Enviado por: {s['vendedor']} ({s['fecha'].split(' ')[0]}) ID: {s['id']}" for s in solicitudes_pendientes]
            sel = st.selectbox("Cargar solicitud para procesar:", opciones)
            if sel != "Seleccione una solicitud...":
                id_sel = sel.split("ID: ")[1]
                solicitud_seleccionada = next((s for s in solicitudes_pendientes if s['id'] == id_sel), None)
    
    with st.container(border=True):
        col_ia1, col_ia2 = st.columns([5, 3], gap="large")
        
        imagen_a_procesar = None
        img_target = None
        
        with col_ia1: 
            if solicitud_seleccionada:
                st.info(f"Visualizando solicitud de: **{solicitud_seleccionada['vendedor']}** (Estado: {solicitud_seleccionada.get('comprobante', 'Pendiente de escaneo')})")
                if os.path.exists(solicitud_seleccionada['ruta_imagen']):
                    img_target = Image.open(solicitud_seleccionada['ruta_imagen'])
                    imagen_a_procesar = img_target 
                    st.image(img_target, use_container_width=True)
                else:
                    st.error("Imagen no encontrada.")
            else:
                imagen_subida = st.file_uploader("Subir boleta o factura (JPG, PNG, WEBP)", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed", key=f"up_ia_{st.session_state.uploader_key}")
                if imagen_subida:
                    imagen_a_procesar = Image.open(imagen_subida)
                    img_target = imagen_a_procesar
                
        with col_ia2:
            st.write("") 
            st.write("") 
            if imagen_a_procesar is not None:
                c_btn_ia1, c_btn_ia2 = st.columns([1, 1])
                with c_btn_ia1:
                    if st.button("Procesar IA", type="primary", disabled=st.session_state.ia_procesado, use_container_width=True):
                        st.session_state.show_download = False 
                        with st.spinner("Analizando..."):
                            try:
                                active_api_key = st.session_state.config_db.get("api_key", "")
                                active_model = st.session_state.config_db.get("model_name", "models/gemini-3.1-flash-lite-preview")
                                genai.configure(api_key=active_api_key)
                                modelo_ia = genai.GenerativeModel(active_model)
                                
                                prompt = """Analiza la boleta o factura con precisión:
                                1. EMISOR (Nombre o Razón Social), 2. RUC_EMISOR, 3. CLIENTE, 4. RUC_DNI_CLIENTE, 5. COMPROBANTE
                                6. VENDEDOR: Extrae el nombre del vendedor.
                                7. CANTIDAD: Extrae la LISTA COMPLETA. El "Total" de la línea debe ser la multiplicación de unidades por metros y DEBE EXPRESARSE EN METROS ("m"). IGNORA LOS PRECIOS.
                                Ejemplo: - 48.00 und x 2.00 m (Rojo, 0.40mm, TR5) - Total: 96.00 m
                                FORMATO ESTRICTO: 
                                EMISOR: X | RUC_EMISOR: X | CLIENTE: X | RUC_DNI_CLIENTE: X | COMPROBANTE: X | VENDEDOR: X | CANTIDAD: X"""
                                
                                respuesta = modelo_ia.generate_content([prompt, img_target])
                                texto = respuesta.text.strip().replace("*", "")
                                
                                datos = {}
                                partes = re.split(r'\s*\|\s*(?=[A-Z_]+:)', texto)
                                for p in partes:
                                    if ":" in p:
                                        k, v = p.split(":", 1)
                                        datos[k.strip()] = v.strip()
                                
                                if "CLIENTE" in datos or "EMISOR" in datos:
                                    extracted_ruc = datos.get("RUC_EMISOR", "").strip()
                                    extracted_ruc_clean = re.sub(r'[^0-9]', '', extracted_ruc)
                                    
                                    allowed_rucs_clean = [re.sub(r'[^0-9]', '', str(e.get("ruc", ""))) for e in st.session_state.empresas if (st.session_state.rol == "administrador" or e["nombre"] in empresas_permitidas_ui) and str(e.get("ruc", "")).strip()]
                                    
                                    if not extracted_ruc_clean or extracted_ruc_clean not in allowed_rucs_clean:
                                        st.session_state.ia_procesado = False
                                        sol_id = solicitud_seleccionada['id'] if solicitud_seleccionada else None
                                        comp_leido = datos.get("COMPROBANTE", "")
                                        modal_alerta_ruc(sol_id, comp_leido)
                                    else:
                                        vendedor_final = solicitud_seleccionada['vendedor'] if solicitud_seleccionada else datos.get("VENDEDOR", "")
                                        comprobante_final = datos.get("COMPROBANTE", "")
                                        
                                        ciudad_final = "Jaén"
                                        for emp in st.session_state.empresas:
                                            if re.sub(r'[^0-9]', '', str(emp.get("ruc", ""))) == extracted_ruc_clean:
                                                dir_full = emp.get("direccion", "Jaén")
                                                ciudad_final = dir_full.split(",")[0].strip() if "," in dir_full else dir_full.strip()
                                                break
                                        
                                        st.session_state.datos_form.update({
                                            "empresa": datos.get("EMISOR", ""), 
                                            "ruc_emisor": datos.get("RUC_EMISOR", ""),
                                            "cliente": datos.get("CLIENTE", ""), 
                                            "ruc": datos.get("RUC_DNI_CLIENTE", ""),
                                            "comprobante": comprobante_final, 
                                            "vendedor": vendedor_final, 
                                            "ciudad": ciudad_final, 
                                            "cantidad": datos.get("CANTIDAD", "")
                                        })
                                        
                                        st.session_state.ia_procesado = True
                                        st.session_state.uploader_key += 1
                                        st.rerun()
                            except Exception as e:
                                st.session_state.ia_procesado = False
                                st.error(f"Error técnico: {e}")
                
                with c_btn_ia2:
                    if st.session_state.ia_procesado:
                        if st.button("Nuevo Escaneo", type="secondary", use_container_width=True):
                            st.session_state.show_download = False
                            limpiar_formulario_emision()
                            st.rerun()
                            
            if solicitud_seleccionada:
                st.write("")
                if st.button("🚫 Rechazar Solicitud", type="secondary", use_container_width=True):
                    comp_actual = st.session_state.datos_form.get("comprobante", "")
                    modal_rechazar_solicitud(solicitud_seleccionada['id'], comp_actual)

    section_header(ICON_DOC, "Datos del cliente y desglose")
    with st.container(border=True):
        bloquear_campos = (st.session_state.rol == "emisor")
        
        uk = st.session_state.uploader_key
        
        c_r1_1, c_r1_2 = st.columns([6, 4], gap="medium")
        empresa_in = c_r1_1.text_input("Empresa Emisora", value=st.session_state.datos_form.get("empresa", ""), disabled=bloquear_campos, key=f"e_in_{uk}")
        st.session_state.datos_form["empresa"] = empresa_in
        
        ruc_emisor_in = c_r1_2.text_input("RUC Emisor", value=st.session_state.datos_form.get("ruc_emisor", ""), disabled=bloquear_campos, key=f"re_in_{uk}")
        st.session_state.datos_form["ruc_emisor"] = ruc_emisor_in
        
        ruc_actual_clean = re.sub(r'[^0-9]', '', st.session_state.datos_form["ruc_emisor"])
        ciudad_dinamica = "Jaén"
        if ruc_actual_clean:
            for emp in st.session_state.empresas:
                if re.sub(r'[^0-9]', '', str(emp.get("ruc", ""))) == ruc_actual_clean:
                    dir_full = emp.get("direccion", "Jaén")
                    ciudad_dinamica = dir_full.split(",")[0].strip() if "," in dir_full else dir_full.strip()
                    break

        c_r2_1, c_r2_2, c_r2_3, c_r2_4, c_r2_5 = st.columns([3, 2, 2, 2, 2], gap="medium")
        st.session_state.datos_form["cliente"] = c_r2_1.text_input("Cliente", value=st.session_state.datos_form.get("cliente", ""), disabled=bloquear_campos, key=f"c_in_{uk}")
        st.session_state.datos_form["ruc"] = c_r2_2.text_input("RUC / DNI", value=st.session_state.datos_form.get("ruc", ""), disabled=bloquear_campos, key=f"r_in_{uk}") 
        st.session_state.datos_form["comprobante"] = c_r2_3.text_input("N° Comprobante", value=st.session_state.datos_form.get("comprobante", ""), placeholder="Ej. F001-000001", disabled=bloquear_campos, key=f"co_in_{uk}")
        st.session_state.datos_form["vendedor"] = c_r2_4.text_input("Vendedor", value=st.session_state.datos_form.get("vendedor", ""), disabled=bloquear_campos, key=f"v_in_{uk}")
        st.session_state.datos_form["ciudad"] = c_r2_5.text_input("Ciudad Emisión", value=ciudad_dinamica, disabled=True, key=f"ci_in_{uk}")
        
        st.session_state.datos_form["cantidad"] = st.text_area("Detalle de Productos (Soporta HTML: <b>, <i>, <br>)", value=st.session_state.datos_form.get("cantidad", ""), height=150, key=f"ca_in_{uk}")
        
        st.write("")
        st.session_state.datos_form["incluir_proteccion"] = st.checkbox("Incluir cláusula de Protección Adicional en este certificado", value=st.session_state.datos_form.get("incluir_proteccion", True), key=f"prot_check_{uk}")
        
        st.write("")
        campos_llenos = len(st.session_state.datos_form["empresa"].strip()) > 0 and len(st.session_state.datos_form["cliente"].strip()) > 0
        col_gen, col_dl = st.columns(2, gap="medium")
        
        with col_gen:
            if st.button("Generar Certificado", type="primary", disabled=not campos_llenos, use_container_width=True):
                comprobante_actual = st.session_state.datos_form["comprobante"].strip()
                ruc_actual_check = st.session_state.datos_form["ruc_emisor"].strip()
                
                ruc_actual_clean_check = re.sub(r'[^0-9]', '', ruc_actual_check)
                allowed_rucs_clean = [re.sub(r'[^0-9]', '', str(e.get("ruc", ""))) for e in st.session_state.empresas if (st.session_state.rol == "administrador" or e["nombre"] in empresas_permitidas_ui) and str(e.get("ruc", "")).strip()]

                if not ruc_actual_clean_check or ruc_actual_clean_check not in allowed_rucs_clean:
                    st.error("🚫 COMPROBANTE NO VÁLIDO: La empresa no está autorizada.")
                elif not comprobante_actual:
                    st.error("⚠️ El número de comprobante no puede estar vacío.")
                elif not es_comprobante_valido(comprobante_actual):
                    st.error("❌ Formato de comprobante inválido. Debe seguir el estándar SUNAT (Ej. F001-1234, B002-5678, E001-901).")
                else:
                    comprobante_duplicado = False
                    for cert in st.session_state.historial_db:
                        if cert.get("Comprobante", "").strip().upper() == comprobante_actual.upper():
                            comprobante_duplicado = True
                            break
                    
                    if comprobante_duplicado:
                        st.error(f"⚠️ Ya existe un certificado emitido para el comprobante N° **{comprobante_actual.upper()}**. No se permiten duplicados.")
                    else:
                        st.session_state.show_download = False
                        num_certificado = datetime.now().strftime("%Y%m%d%H%M%S")
                        
                        ciudad_final_gen = ciudad_dinamica
                        for emp in st.session_state.empresas:
                            if re.sub(r'[^0-9]', '', str(emp.get("ruc", ""))) == ruc_actual_clean_check:
                                dir_full = emp.get("direccion", "Jaén")
                                ciudad_final_gen = dir_full.split(",")[0].strip() if "," in dir_full else dir_full.strip()
                                break
                        
                        with st.spinner("Construyendo documento seguro..."):
                            pdf_bytes = generar_pdf(
                                st.session_state.datos_form["empresa"], st.session_state.datos_form["ruc_emisor"], 
                                st.session_state.datos_form["cliente"], st.session_state.datos_form["ruc"], 
                                comprobante_actual.upper(), st.session_state.datos_form["vendedor"],
                                ciudad_final_gen, st.session_state.propiedades_dinamicas, 
                                st.session_state.datos_form["cantidad"], st.session_state.caracteristicas_18, 
                                st.session_state.mensaje_final, num_certificado, 
                                st.session_state.datos_form["incluir_proteccion"], st.session_state.config_db.get("texto_adicional", "")
                            )
                            
                            pdf_filename = f"Certificado_{st.session_state.datos_form['ruc']}_{num_certificado}.pdf"
                            pdf_filepath = os.path.join("certificados_emitidos", pdf_filename)
                            with open(pdf_filepath, "wb") as f:
                                f.write(pdf_bytes)
                            
                            nuevo_registro = {
                                "N_Cert": num_certificado, 
                                "Fecha": datetime.now().strftime("%d/%m/%Y"),
                                "Empresa_Emisora": st.session_state.datos_form["empresa"], 
                                "Usuario_Emisor": st.session_state.usuario_actual,
                                "Cliente": st.session_state.datos_form["cliente"],
                                "Documento": st.session_state.datos_form["ruc"], 
                                "Comprobante": comprobante_actual.upper(),
                                "Vendedor": st.session_state.datos_form["vendedor"], 
                                "Ciudad": ciudad_final_gen, 
                                "Estado": "Emitido", 
                                "Ruta_PDF": pdf_filepath
                            }
                            st.session_state.historial_db.append(nuevo_registro)
                            guardar_historial(st.session_state.historial_db)
                            
                            if solicitud_seleccionada:
                                for idx, sol in enumerate(st.session_state.solicitudes):
                                    if sol['id'] == solicitud_seleccionada['id']:
                                        st.session_state.solicitudes[idx]['estado'] = 'Completado'
                                st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
                                guardar_configuracion(st.session_state.config_db)
                            
                            st.session_state.ultimo_pdf_ruta = pdf_filepath
                            st.session_state.show_download = True
                            limpiar_formulario_emision()
                            st.rerun()

        with col_dl:
            if st.session_state.get('show_download', False) and st.session_state.ultimo_pdf_ruta and os.path.exists(st.session_state.ultimo_pdf_ruta):
                with open(st.session_state.ultimo_pdf_ruta, "rb") as f:
                    b64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    file_n = os.path.basename(st.session_state.ultimo_pdf_ruta)
                    dl_link = f'''
                    <a href="data:application/pdf;base64,{b64_pdf}" download="{file_n}" 
                       style="display: flex; align-items: center; justify-content: center; gap: 10px; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 0.6rem 1.5rem; border-radius: 999px; text-decoration: none; font-weight: 600; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); transition: all 0.3s ease;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        DESCARGAR PDF
                    </a>
                    '''
                    st.markdown(dl_link, unsafe_allow_html=True)

def tab_configuracion_diseno():
    section_header(ICON_BUILDING, "Catálogo de Empresas")
    with st.container(border=True):
        st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>AÑADIR EMPRESA AL SISTEMA</p>", unsafe_allow_html=True)
        with st.form("form_add_emp", clear_on_submit=True):
            c_cat1, c_cat2, c_cat3 = st.columns([1, 1, 1], gap="medium")
            nueva_empresa = c_cat1.text_input("Razón Social", placeholder="Ej. ACEROSNOR S.A.C.")
            nuevo_ruc = c_cat2.text_input("RUC (Obligatorio para validación)", placeholder="Ej. 20123456789")
            nueva_dir = c_cat3.text_input("Dirección", placeholder="Ej. Jaén, Cajamarca")
            
            if st.form_submit_button("Añadir al catálogo", type="primary", use_container_width=True):
                if not nueva_empresa.strip() or not nuevo_ruc.strip():
                    st.error("⚠️ La Razón Social y el RUC son OBLIGATORIOS para la seguridad del sistema.")
                elif not any(e["nombre"].upper() == nueva_empresa.upper() for e in st.session_state.empresas):
                    st.session_state.empresas.append({"nombre": nueva_empresa.upper(), "ruc": nuevo_ruc.strip(), "direccion": nueva_dir})
                    st.session_state.config_db["empresas"] = st.session_state.empresas
                    guardar_configuracion(st.session_state.config_db)
                    st.rerun()

    with st.container(border=True):
        st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>DIRECTORIO DE EMPRESAS PERMITIDAS</p>", unsafe_allow_html=True)
        for emp in list(st.session_state.empresas):
            col_e1, col_e2, col_e3, col_e4 = st.columns([3, 2, 3, 2])
            col_e1.markdown(f"<span style='color: #1E293B; font-weight:600; font-size:1rem;'>{emp['nombre']}</span>", unsafe_allow_html=True)
            col_e2.markdown(f"<span style='color: #64748B; font-size:0.9rem;'>RUC: {emp.get('ruc', 'N/A')}</span>", unsafe_allow_html=True)
            col_e3.markdown(f"<span style='color: #64748B; font-size:0.9rem;'>{emp.get('direccion', '')}</span>", unsafe_allow_html=True)
            
            if len(st.session_state.empresas) > 1:
                if col_e4.button("🗑️ Eliminar", key=f"del_emp_{emp['nombre']}", type="secondary", use_container_width=True):
                    st.session_state.empresas = [e for e in st.session_state.empresas if e['nombre'] != emp['nombre']]
                    st.session_state.config_db["empresas"] = st.session_state.empresas
                    guardar_configuracion(st.session_state.config_db)
                    st.rerun()
            else:
                col_e4.markdown("<span style='font-size:0.85rem; color:#94A3B8;'>Obligatoria</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

    section_header(ICON_IMAGE, "Identidad Visual, Plantillas y Firmas")
    with st.container(border=True):
        nombres_empresas = [e["nombre"] for e in st.session_state.empresas]
        emp_visual = st.selectbox("Seleccione empresa a configurar:", nombres_empresas)
        if emp_visual:
            st.write("")
            c_img1, c_img2 = st.columns([1, 1], gap="large")
            with c_img1:
                st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>LOGO CORPORATIVO</p>", unsafe_allow_html=True)
                ruta_l = obtener_ruta_logo(emp_visual)
                if os.path.exists(ruta_l):
                    st.markdown(obtener_imagen_html(ruta_l), unsafe_allow_html=True)
                    if st.button("🗑️ Quitar Logo", key="dl_btn", type="secondary", use_container_width=True): os.remove(ruta_l); st.rerun()
                else:
                    st.markdown('<div style="height: 100px; display: flex; align-items: center; justify-content: center; border: 2px dashed #E2E8F0; border-radius: 12px; margin-bottom: 15px; color: #94A3B8;">Sin logo</div>', unsafe_allow_html=True)
                    file_l = st.file_uploader("Subir logo", type=["png", "jpg"], key="ul_btn", label_visibility="collapsed")
                    if file_l and st.button("Guardar Logo", key="sl_btn", type="primary", use_container_width=True):
                        img = Image.open(file_l)
                        img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                        img.save(ruta_l, format=img.format)
                        st.rerun()
                        
            with c_img2:
                st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>PLANTILLA FONDO (.PDF)</p>", unsafe_allow_html=True)
                ruta_p = obtener_ruta_plantilla(emp_visual)
                if os.path.exists(ruta_p):
                    st.markdown('''
                        <div style="height: 100px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px solid #10B981; border-radius: 12px; margin-bottom: 15px; background-color: #ECFDF5;">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M16 13H8"></path><path d="M16 17H8"></path><path d="M10 9H8"></path></svg>
                            <span style="color: #10B981; font-weight: bold; margin-top: 5px;">Plantilla Guardada</span>
                        </div>
                    ''', unsafe_allow_html=True)
                    if st.button("🗑️ Quitar Plantilla", key="dp_btn", type="secondary", use_container_width=True): os.remove(ruta_p); st.rerun()
                else:
                    st.markdown('<div style="height: 100px; display: flex; align-items: center; justify-content: center; border: 2px dashed #E2E8F0; border-radius: 12px; margin-bottom: 15px; color: #94A3B8; text-align:center;">Sube diseño en .PDF</div>', unsafe_allow_html=True)
                    file_p = st.file_uploader("Subir diseño en .PDF", type=["pdf"], key="up_p_btn", label_visibility="collapsed")
                    if file_p and st.button("Guardar Plantilla", key="sp_p_btn", type="primary", use_container_width=True):
                        with open(ruta_p, "wb") as f: f.write(file_p.getbuffer())
                        st.rerun()
                        
            st.markdown("<hr style='margin: 25px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>FIRMAS AUTORIZADAS</p>", unsafe_allow_html=True)
            
            firmas_emp = st.session_state.config_db.get("firmas_config", {}).get(emp_visual, [])
            
            with st.form(f"form_add_firma_{emp_visual}", clear_on_submit=True):
                st.markdown("<span style='font-size:0.85rem; font-weight:600; color:#64748B;'>Añadir Nueva Firma</span>", unsafe_allow_html=True)
                c_f_add1, c_f_add2, c_f_add3 = st.columns([2, 2, 1], vertical_alignment="bottom")
                new_f_file = c_f_add1.file_uploader("Sube la firma (.png, .jpg)", type=["png", "jpg"], label_visibility="collapsed")
                new_f_cargo = c_f_add2.text_input("Cargo", placeholder="Ej. GERENTE GENERAL", label_visibility="collapsed")
                if c_f_add3.form_submit_button("Guardar Firma", type="primary", use_container_width=True):
                    if new_f_file and new_f_cargo.strip():
                        f_id = uuid.uuid4().hex[:8]
                        f_path = os.path.join(os.getcwd(), f"firma_{limpiar_nombre(emp_visual)}_{f_id}.png")
                        with open(f_path, "wb") as f: f.write(new_f_file.getbuffer())
                        f_dict = st.session_state.config_db.get("firmas_config", {})
                        if emp_visual not in f_dict: f_dict[emp_visual] = []
                        f_dict[emp_visual].append({"id": f_id, "cargo": new_f_cargo.strip()})
                        st.session_state.config_db["firmas_config"] = f_dict
                        guardar_configuracion(st.session_state.config_db)
                        st.rerun()
                        
            st.write("")
            if firmas_emp:
                cols_firmas = st.columns(4, gap="medium")
                for idx, f_data in enumerate(firmas_emp):
                    with cols_firmas[idx % 4].container(border=True):
                        f_path = os.path.join(os.getcwd(), f"firma_{limpiar_nombre(emp_visual)}_{f_data['id']}.png")
                        if os.path.exists(f_path):
                            st.markdown(obtener_imagen_html(f_path, altura_px=50), unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='height: 50px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; color:#94A3B8; font-size:0.8rem;'>Sin imagen</div>", unsafe_allow_html=True)
                        
                        st.markdown(f"<div style='text-align:center; color: #1E293B; font-size:0.9rem; font-weight:700; margin-bottom: 10px;'>{f_data['cargo'].upper()}</div>", unsafe_allow_html=True)
                        
                        if st.button("🗑️ Eliminar", key=f"del_f_{f_data['id']}", type="secondary", use_container_width=True):
                            if os.path.exists(f_path): os.remove(f_path)
                            firmas_emp.remove(f_data)
                            st.session_state.config_db.setdefault("firmas_config", {})[emp_visual] = firmas_emp
                            guardar_configuracion(st.session_state.config_db)
                            st.rerun()
            else:
                st.info("No hay firmas registradas para esta empresa.")

    section_header(ICON_TYPE, "Configuración de Contenido Fijo")
    with st.container(border=True):
        st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>CARACTERÍSTICAS GENERALES</p>", unsafe_allow_html=True)
        for idx_dyn, prop_dyn in enumerate(st.session_state.propiedades_dinamicas):
            col_d1, col_d2, col_d3 = st.columns([4, 5, 2])
            uid = prop_dyn['id']
            st.session_state.propiedades_dinamicas[idx_dyn]['label'] = col_d1.text_input(f"Etiqueta {idx_dyn+1}", value=prop_dyn['label'], key=f"edit_dyn_lbl_{uid}")
            st.session_state.propiedades_dinamicas[idx_dyn]['default'] = col_d2.text_input(f"Valor {idx_dyn+1}", value=prop_dyn['default'], key=f"edit_dyn_val_{uid}")
            if col_d3.button("🗑️ Eliminar", key=f"del_dyn_{uid}", type="secondary"):
                st.session_state.propiedades_dinamicas.pop(idx_dyn)
                st.rerun()
        
        with st.form("form_add_carac", clear_on_submit=True):
            c_car1, c_car2, c_car3 = st.columns([4, 5, 2], gap="medium")
            nueva_lbl = c_car1.text_input("Nueva Etiqueta", placeholder="Ej. ACABADO")
            nuevo_val = c_car2.text_input("Nuevo Valor", placeholder="Ej. MATE")
            if c_car3.form_submit_button("Añadir", type="primary"):
                if nueva_lbl and nuevo_val:
                    st.session_state.propiedades_dinamicas.append({"id": str(uuid.uuid4()), "label": nueva_lbl, "default": nuevo_val, "current": nuevo_val})
                    st.session_state.config_db["propiedades_dinamicas"] = st.session_state.propiedades_dinamicas
                    guardar_configuracion(st.session_state.config_db)
                    st.rerun()

    with st.container(border=True):
        st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>GESTOR DE TIPOGRAFÍAS (.TTF)</p>", unsafe_allow_html=True)
        c_f1, c_f2 = st.columns([3,1])
        fuente_up = c_f1.file_uploader("Subir fuente", type=["ttf"], label_visibility="collapsed")
        if fuente_up:
            if c_f2.button("Instalar Tipografía", type="primary", use_container_width=True):
                n_f = fuente_up.name.split(".")[0]
                with open(obtener_ruta_fuente(n_f), "wb") as f: f.write(fuente_up.getbuffer())
                if n_f not in st.session_state.fuentes_custom: st.session_state.fuentes_custom.append(n_f)
                st.rerun()

    fuentes_disp = ["Arial", "Times", "Courier"] + st.session_state.fuentes_custom
    alineaciones = {"Izquierda": "L", "Centro": "C", "Derecha": "R", "Justificado": "J"}
    
    with st.container(border=True):
        st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>TEXTOS DEL DOCUMENTO (Soporta HTML)</p>", unsafe_allow_html=True)
        
        f1, f2, f3, f4 = st.columns(4, gap="medium")
        st.session_state.fuente_intro = f1.selectbox("Fuente Cabecera", fuentes_disp, index=fuentes_disp.index(st.session_state.fuente_intro) if st.session_state.fuente_intro in fuentes_disp else 0, key="fi")
        st.session_state.tamano_intro = f2.number_input("Tamaño Cabecera", 8, 20, st.session_state.tamano_intro, key="ti")
        st.session_state.align_intro = alineaciones[f3.selectbox("Alineación Cabecera", list(alineaciones.keys()), index=list(alineaciones.values()).index(st.session_state.align_intro), key="ai")]
        st.session_state.linea_intro = f4.number_input("Interlineado Cabecera", 3, 10, st.session_state.linea_intro, key="li")
        st.session_state.mensaje_intro = st.text_area("Texto de Cabecera", st.session_state.mensaje_intro, height=80, label_visibility="collapsed")
        
        st.markdown("<hr style='margin: 20px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        st.write("**Características inferiores**")
        st.session_state.caracteristicas_18 = st.text_area("Listado de características técnicas", st.session_state.caracteristicas_18, height=80, label_visibility="collapsed")
        
        st.markdown("<hr style='margin: 20px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        st.write("**Información Adicional (Auto-enumerada)**")
        st.session_state.titulo_adicional = st.text_input("Título de la sección", value=st.session_state.config_db.get("titulo_adicional", "PROTECCIÓN ADICIONAL"))
        st.session_state.texto_adicional = st.text_area("Contenido base", value=st.session_state.config_db.get("texto_adicional", ""), height=80, label_visibility="collapsed")
        
        st.markdown("<hr style='margin: 20px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        st.write("**Sección Cierre**")
        f5, f6, f7, f8 = st.columns(4, gap="medium")
        st.session_state.fuente_final = f5.selectbox("Fuente Cierre", fuentes_disp, index=fuentes_disp.index(st.session_state.fuente_final) if st.session_state.fuente_final in fuentes_disp else 0, key="ff")
        st.session_state.tamano_final = f6.number_input("Tamaño Cierre", 8, 20, st.session_state.tamano_final, key="tf")
        st.session_state.align_final = alineaciones[f7.selectbox("Alineación Cierre", list(alineaciones.keys()), index=list(alineaciones.values()).index(st.session_state.align_final), key="af")]
        st.session_state.linea_final = f8.number_input("Interlineado Cierre", 3, 10, st.session_state.linea_final, key="lf")
        st.session_state.mensaje_final = st.text_area("Cierre", st.session_state.mensaje_final, height=60, label_visibility="collapsed")

    st.write("")
    c_btn_save1, c_btn_save2, c_btn_save3 = st.columns([1, 2, 1])
    with c_btn_save2:
        if st.button("Guardar Configuración General", type="primary", use_container_width=True):
            st.session_state.config_db.update({
                "usuarios": st.session_state.usuarios, 
                "empresas": st.session_state.empresas,
                "propiedades_dinamicas": st.session_state.propiedades_dinamicas, 
                "lista_carac": st.session_state.lista_carac,
                "mensaje_intro": st.session_state.mensaje_intro, 
                "fuente_intro": st.session_state.fuente_intro,
                "tamano_intro": st.session_state.tamano_intro, 
                "align_intro": st.session_state.align_intro,
                "linea_intro": st.session_state.linea_intro, 
                "caracteristicas_18": st.session_state.caracteristicas_18,
                "titulo_adicional": st.session_state.titulo_adicional,
                "texto_adicional": st.session_state.texto_adicional,
                "mensaje_final": st.session_state.mensaje_final, 
                "fuente_final": st.session_state.fuente_final,
                "tamano_final": st.session_state.tamano_final, 
                "align_final": st.session_state.align_final,
                "linea_final": st.session_state.linea_final
            })
            guardar_configuracion(st.session_state.config_db)
            st.success("¡Configuración guardada de forma permanente!")
            time.sleep(1.5)
            st.rerun()

def tab_ajustes_sistema():
    section_header(ICON_SETTINGS, "Credenciales del Motor IA")
    with st.container(border=True):
        st.markdown("<p style='font-size:0.95rem; color:#64748B;'>Configure las credenciales de la API de Google Gemini y el modelo activo. Los cambios se aplican de inmediato en todo el sistema.</p>", unsafe_allow_html=True)
        with st.form("form_ajustes_ia", clear_on_submit=False):
            input_api_key = st.text_input("Clave API Google Gemini", value=st.session_state.config_db.get("api_key", ""), type="password")
            input_model = st.text_input("Modelo IA Activo", value=st.session_state.config_db.get("model_name", "models/gemini-3.1-flash-lite-preview"))
            st.write("")
            if st.form_submit_button("Guardar Credenciales", type="primary", use_container_width=True):
                if input_api_key.strip() and input_model.strip():
                    st.session_state.config_db["api_key"] = input_api_key.strip()
                    st.session_state.config_db["model_name"] = input_model.strip()
                    guardar_configuracion(st.session_state.config_db)
                    st.success("¡Credenciales actualizadas correctamente!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Los campos no pueden estar vacíos.")

def tab_usuarios():
    section_header(ICON_USERS, "Gestión de Usuarios")
    
    todas_empresas_nombres = [e["nombre"] for e in st.session_state.empresas]
    
    with st.container(border=True):
        c_us1, c_us2 = st.columns([1, 2], gap="large")
        with c_us1:
            st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>CREAR O EDITAR</p>", unsafe_allow_html=True)
            with st.form("form_users", clear_on_submit=True):
                n_usr = st.text_input("Usuario")
                n_pass = st.text_input("Contraseña", type="password")
                n_rol = st.selectbox("Rol", ["administrador", "emisor", "vendedor"])
                n_empresas = st.multiselect("Empresas Permitidas", todas_empresas_nombres, default=todas_empresas_nombres)
                
                st.write("")
                if st.form_submit_button("Guardar Usuario", type="primary", use_container_width=True):
                    if not n_usr.strip() or not n_pass.strip():
                        st.error("⚠️ Ingrese datos válidos.")
                    elif not n_empresas:
                        st.error("⚠️ Debe asignar al menos una empresa.")
                    else:
                        st.session_state.usuarios[n_usr.strip()] = {"clave": n_pass.strip(), "rol": n_rol, "empresas_permitidas": n_empresas}
                        st.session_state.config_db["usuarios"] = st.session_state.usuarios
                        guardar_configuracion(st.session_state.config_db)
                        st.rerun()
        with c_us2:
            st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>DIRECTORIO ACTIVO</p>", unsafe_allow_html=True)
            c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 2, 3, 2, 2])
            c_h1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>USUARIO</span>", unsafe_allow_html=True)
            c_h2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>ROL</span>", unsafe_allow_html=True)
            c_h3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>EMPRESAS</span>", unsafe_allow_html=True)
            c_h4.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>CLAVE</span>", unsafe_allow_html=True)
            c_h5.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>ACCIÓN</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

            for u, dat in list(st.session_state.usuarios.items()):
                if u == "cliente_acceso": continue
                
                col_row1, col_row2, col_row3, col_row4, col_row5 = st.columns([2, 2, 3, 2, 2], vertical_alignment="center")
                col_row1.markdown(f"<span style='color: #1E293B; font-weight:600;'>{u}</span>", unsafe_allow_html=True)
                col_row2.markdown(f"<span style='color:#64748B;'>{dat['rol'].capitalize()}</span>", unsafe_allow_html=True)
                
                emps = dat.get("empresas_permitidas", ["Todas (Migración)"])
                emps_str = ", ".join(emps) if len(emps) <= 2 else f"{len(emps)} asignadas"
                col_row3.markdown(f"<span style='color:#64748B; font-size:0.85rem;'>{emps_str}</span>", unsafe_allow_html=True)
                
                if col_row4.button("Ver", key=f"btn_ver_{u}", type="secondary"):
                    modal_verificar_clave(u)
                if u != st.session_state.usuario_actual:
                    if col_row5.button("🗑️", key=f"btn_del_{u}", type="secondary"):
                        modal_confirmar_eliminacion(u)
                else:
                    col_row5.markdown("<span style='font-size:0.85rem; color:#94A3B8;'>Actual</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)

def tab_historial_general():
    section_header(ICON_HISTORY, "Registro Histórico")
    
    def limpiar_texto_empresa(texto):
        if not texto: return ""
        t = str(texto).upper()
        t = re.sub(r'[.,\-_/]', ' ', t)
        t = re.sub(r'\bS\s*A\s*C\b', 'SAC', t)
        t = re.sub(r'\bS\s*A\b', 'SA', t)
        t = re.sub(r'\bE\s*I\s*R\s*L\b', 'EIRL', t)
        return re.sub(r'\s+', ' ', t).strip()

    emisor_empresas = st.session_state.usuarios.get(st.session_state.usuario_actual, {}).get("empresas_permitidas", [])
    emisor_empresas_norm = [limpiar_texto_empresa(e) for e in emisor_empresas]
    
    def puede_ver_solicitud(sol):
        if st.session_state.rol == 'administrador': return True
        vendedor_req = sol.get('vendedor', '')
        vendor_empresas = st.session_state.usuarios.get(vendedor_req, {}).get("empresas_permitidas", [])
        if not vendor_empresas: return True
        vendor_empresas_norm = [limpiar_texto_empresa(e) for e in vendor_empresas]
        return any(emp in emisor_empresas_norm for emp in vendor_empresas_norm)

    if st.session_state.rol == "administrador":
        historial_filtrado = st.session_state.historial_db
    else:
        historial_filtrado = [c for c in st.session_state.historial_db if limpiar_texto_empresa(c.get("Empresa_Emisora", c.get("Emisor", ""))) in emisor_empresas_norm]

    rechazadas_filtradas = [s for s in st.session_state.solicitudes if s['estado'] == 'Rechazado' and puede_ver_solicitud(s)]

    st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>CERTIFICADOS EMITIDOS</p>", unsafe_allow_html=True)
    with st.container(border=True):
        if len(historial_filtrado) > 0:
            is_admin = (st.session_state.rol == "administrador")
            
            if is_admin:
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 2.5, 2, 2.5, 1.5, 1.5, 1.0, 1.0])
                c8.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px; display:block; text-align:center;'>ACCIÓN</span>", unsafe_allow_html=True)
            else:
                c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2.5, 2, 2.5, 1.5, 1.5, 1.0])
                
            c1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>FECHA</span>", unsafe_allow_html=True)
            c2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>EMPRESA</span>", unsafe_allow_html=True)
            c3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>COMPROBANTE</span>", unsafe_allow_html=True)
            c4.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>CLIENTE</span>", unsafe_allow_html=True)
            c5.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>VENDEDOR</span>", unsafe_allow_html=True)
            c6.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px;'>EMISOR</span>", unsafe_allow_html=True)
            c7.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.75rem; letter-spacing:0.5px; display:block; text-align:center;'>DOC.</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            
            for cert in reversed(historial_filtrado):
                if is_admin:
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 2.5, 2, 2.5, 1.5, 1.5, 1.0, 1.0], vertical_alignment="center")
                else:
                    c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2.5, 2, 2.5, 1.5, 1.5, 1.0], vertical_alignment="center")
                    
                c1.write(cert["Fecha"])
                c2.write(cert.get("Empresa_Emisora", cert.get("Emisor", "")))
                c3.write(cert["Comprobante"])
                c4.write(cert["Cliente"])
                c5.write(cert.get("Vendedor", ""))
                c6.write(cert.get("Usuario_Emisor", "Admin")) 
                
                ruta = cert.get("Ruta_PDF")
                if ruta and os.path.exists(ruta):
                    c7.markdown(f"<div style='text-align:center;'>{get_download_icon(ruta)}</div>", unsafe_allow_html=True)
                else:
                    c7.markdown("<div style='text-align:center;'><span style='color:#EF4444; font-size:0.85rem;'>N/A</span></div>", unsafe_allow_html=True)
                    
                if is_admin:
                    if c8.button("🗑️", key=f"del_cert_{cert['N_Cert']}", help="Eliminar certificado", use_container_width=True):
                        st.session_state.historial_db = [c for c in st.session_state.historial_db if c['N_Cert'] != cert['N_Cert']]
                        guardar_historial(st.session_state.historial_db)
                        if ruta and os.path.exists(ruta):
                            try: os.remove(ruta)
                            except: pass
                        st.rerun()
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.info("Aún no hay certificados emitidos en la base de datos para esta sede.")

    st.write("")
    st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>SOLICITUDES RECHAZADAS</p>", unsafe_allow_html=True)
    with st.container(border=True):
        if len(rechazadas_filtradas) > 0:
            is_admin = (st.session_state.rol == "administrador")
            
            if is_admin:
                c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 4, 1])
                c5.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px; display:block; text-align:center;'>ACCIÓN</span>", unsafe_allow_html=True)
            else:
                c1, c2, c3, c4 = st.columns([2, 2, 2, 6])
                
            c1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>FECHA</span>", unsafe_allow_html=True)
            c2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>COMPROBANTE</span>", unsafe_allow_html=True)
            c3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>VENDEDOR</span>", unsafe_allow_html=True)
            c4.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>MOTIVO DEL RECHAZO</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            
            for s in reversed(rechazadas_filtradas):
                if is_admin:
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 4, 1], vertical_alignment="center")
                else:
                    c1, c2, c3, c4 = st.columns([2, 2, 2, 6], vertical_alignment="center")
                    
                c1.write(s['fecha'].split(' ')[0])
                c2.write(f"N° {s.get('comprobante', 'S/N')}")
                c3.write(s['vendedor'])
                c4.markdown(f"<span style='color:#B91C1C; font-size:0.85rem;'>{s.get('motivo_rechazo', '')}</span>", unsafe_allow_html=True)
                
                if is_admin:
                    if c5.button("🗑️", key=f"del_rech_gen_{s['id']}", help="Eliminar solicitud", use_container_width=True):
                        st.session_state.solicitudes = [req for req in st.session_state.solicitudes if req['id'] != s['id']]
                        st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
                        guardar_configuracion(st.session_state.config_db)
                        st.rerun()
                        
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.info("No tienes solicitudes rechazadas en el historial.")

def tab_solicitar_vendedor():
    section_header(ICON_DOC, "Solicitar Certificado")
    with st.container(border=True):
        st.write("Sube o pega la captura de pantalla de la boleta/factura. El área de emisión extraerá los datos y validará el documento de forma oficial.")
        
        with st.form("form_solicitud", clear_on_submit=True):
            foto = st.file_uploader("Fotografía o Captura (Obligatorio)", type=["png", "jpg", "jpeg", "webp"])
            notas = st.text_area("Notas (Opcional)")
            st.write("")
            if st.form_submit_button("Enviar Solicitud", type="primary", use_container_width=True):
                if foto is None:
                    st.error("⚠️ Es obligatorio subir la fotografía o captura de pantalla.")
                else:
                    file_id = str(uuid.uuid4())[:8]
                    file_path = os.path.join("solicitudes_img", f"req_{file_id}.png")
                    with open(file_path, "wb") as f:
                        f.write(foto.getbuffer())
                    
                    vendedor_empresas = st.session_state.usuarios[st.session_state.usuario_actual].get("empresas_permitidas", [])
                    
                    nueva_sol = {
                        "id": file_id, 
                        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "vendedor": st.session_state.usuario_actual,
                        "empresas_vendedor": vendedor_empresas,
                        "comprobante": "Por escanear", 
                        "ruta_imagen": file_path,
                        "notas": notas, 
                        "estado": "Pendiente"
                    }
                    st.session_state.solicitudes.append(nueva_sol)
                    st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
                    guardar_configuracion(st.session_state.config_db)
                    st.success("✅ ¡Solicitud enviada! El emisor procesará la imagen con Inteligencia Artificial.")
                    time.sleep(1.5)
                    st.rerun()

    st.write("")
    st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>MIS SOLICITUDES PENDIENTES</p>", unsafe_allow_html=True)
    with st.container(border=True):
        mis_sols = [s for s in st.session_state.solicitudes if s['vendedor'] == st.session_state.usuario_actual and s['estado'] != 'Rechazado']
        if mis_sols:
            c1, c2, c3 = st.columns([3, 4, 3])
            c1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>FECHA</span>", unsafe_allow_html=True)
            c2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>COMPROBANTE</span>", unsafe_allow_html=True)
            c3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>ESTADO</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

            for s in reversed(mis_sols):
                c1, c2, c3 = st.columns([3, 4, 3], vertical_alignment="center")
                c1.write(s['fecha'].split(' ')[0])
                c2.write(f"N° {s.get('comprobante', 'S/N')}")
                
                color_estado = "#10B981" if s['estado'] == 'Completado' else "#F59E0B"
                c3.markdown(f"<span style='color:{color_estado}; font-weight:600;'>{s['estado']}</span>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.info("No tienes solicitudes en proceso.")

def tab_historial_vendedor():
    section_header(ICON_HISTORY, "Mis Certificados")
    
    st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>CERTIFICADOS EMITIDOS (DESCARGAS)</p>", unsafe_allow_html=True)
    with st.container(border=True):
        mis_certificados = [c for c in st.session_state.historial_db if c.get("Vendedor") == st.session_state.usuario_actual]
        if mis_certificados:
            c1, c2, c3, c4 = st.columns([2, 3, 4, 1])
            c1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>FECHA</span>", unsafe_allow_html=True)
            c2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>COMPROBANTE</span>", unsafe_allow_html=True)
            c3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>CLIENTE</span>", unsafe_allow_html=True)
            c4.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px; display:block; text-align:center;'>DOC.</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            
            for cert in reversed(mis_certificados):
                c1, c2, c3, c4 = st.columns([2, 3, 4, 1], vertical_alignment="center")
                c1.write(cert["Fecha"])
                c2.write(cert["Comprobante"])
                c3.write(cert["Cliente"])
                ruta = cert.get("Ruta_PDF")
                if ruta and os.path.exists(ruta):
                    c4.markdown(f"<div style='text-align:center;'>{get_download_icon(ruta)}</div>", unsafe_allow_html=True)
                else:
                    c4.markdown("<div style='text-align:center;'><span style='color:#94A3B8;'>N/A</span></div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.info("Aún no tienes certificados emitidos vinculados a tu usuario.")

    st.write("")
    st.markdown("<p style='font-weight:600; color:#4E008E; margin-bottom:15px; font-size:0.85rem; letter-spacing:0.5px;'>SOLICITUDES RECHAZADAS</p>", unsafe_allow_html=True)
    with st.container(border=True):
        mis_rechazados = [s for s in st.session_state.solicitudes if s['vendedor'] == st.session_state.usuario_actual and s['estado'] == 'Rechazado']
        if mis_rechazados:
            c1, c2, c3 = st.columns([2, 3, 5])
            c1.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>FECHA</span>", unsafe_allow_html=True)
            c2.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>COMPROBANTE</span>", unsafe_allow_html=True)
            c3.markdown("<span style='color:#94A3B8; font-weight:600; font-size:0.8rem; letter-spacing:0.5px;'>MOTIVO DEL RECHAZO</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
            
            for s in reversed(mis_rechazados):
                c1, c2, c3 = st.columns([2, 3, 5], vertical_alignment="center")
                c1.write(s['fecha'].split(' ')[0])
                c2.write(f"N° {s.get('comprobante', 'S/N')}")
                c3.markdown(f"<span style='color:#B91C1C; font-size:0.85rem;'>{s.get('motivo_rechazo', '')}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
        else:
            st.info("No tienes solicitudes rechazadas.")

def vista_verificacion_publica():
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 40px;'>
            <div style='display: inline-block; background-color: #F3E8FF; padding: 20px; border-radius: 50%; margin-bottom: 15px;'>
                <svg width="45" height="45" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><circle cx="10" cy="13" r="2"></circle><line x1="11.4" y1="14.4" x2="13.5" y2="16.5"></line></svg>
            </div>
            <h2 style='color: #1E293B; font-weight: 800; letter-spacing: -0.5px;'>Verificación de Certificados</h2>
            <p style='color: #64748B; font-size: 1.1rem; max-width: 600px; margin: 0 auto;'>Ingrese los datos exactos de su comprobante para buscar y descargar su certificado de calidad.</p>
        </div>
    """, unsafe_allow_html=True)
    
    nombres_empresas = [e["nombre"] for e in st.session_state.empresas]
    
    with st.container(border=True):
        with st.form("form_verificacion", border=False):
            c1, c2, c3 = st.columns(3, gap="medium")
            empresa_verif = c1.selectbox("Empresa Emisora", nombres_empresas)
            comp_verif = c2.text_input("N° de Comprobante", placeholder="Ej. F001-000001")
            doc_verif = c3.text_input("Su RUC / DNI", placeholder="Documento del cliente")
            
            st.write("")
            verificar_btn = st.form_submit_button("Buscar Certificado", type="primary", use_container_width=True)
            
        if verificar_btn:
            if not comp_verif.strip() or not doc_verif.strip():
                st.error("⚠️ Por favor, ingrese el número de comprobante y su documento de identidad.")
            else:
                def limpiar_texto_buscador(s):
                    if not s: return ""
                    t = str(s).upper()
                    t = re.sub(r'[.,\-_/]', ' ', t)
                    t = re.sub(r'\bS\s*A\s*C\b', 'SAC', t)
                    t = re.sub(r'\bS\s*A\b', 'SA', t)
                    t = re.sub(r'\bE\s*I\s*R\s*L\b', 'EIRL', t)
                    return re.sub(r'\s+', '', t)
                
                doc_in = re.sub(r'[^0-9]', '', str(doc_verif))
                comp_in = limpiar_texto_buscador(comp_verif)
                emp_in = limpiar_texto_buscador(empresa_verif)
                
                encontrado = None
                for cert in st.session_state.historial_db:
                    doc_db = re.sub(r'[^0-9]', '', str(cert.get("Documento", "")))
                    comp_db = limpiar_texto_buscador(cert.get("Comprobante", ""))
                    emp_db = limpiar_texto_buscador(cert.get("Empresa_Emisora", cert.get("Emisor", "")))
                    
                    if comp_db == comp_in and emp_db == emp_in and doc_db == doc_in:
                        encontrado = cert
                        break
                        
                if encontrado:
                    st.success("✅ ¡Certificado validado y encontrado con éxito!")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    c_h1, c_h2, c_h3, c_h4, c_h5 = st.columns([2, 2, 2, 3, 1])
                    c_h1.markdown("<span style='color:#94A3B8; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;'>N° CERTIFICADO</span>", unsafe_allow_html=True)
                    c_h2.markdown("<span style='color:#94A3B8; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;'>FECHA EMISIÓN</span>", unsafe_allow_html=True)
                    c_h3.markdown("<span style='color:#94A3B8; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;'>VENDEDOR</span>", unsafe_allow_html=True)
                    c_h4.markdown("<span style='color:#94A3B8; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;'>EMPRESA</span>", unsafe_allow_html=True)
                    c_h5.markdown("<span style='color:#94A3B8; font-weight:700; font-size:0.8rem; letter-spacing:0.5px; display:block; text-align:center;'>DOC.</span>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 8px 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
                    
                    c_d1, c_d2, c_d3, c_d4, c_d5 = st.columns([2, 2, 2, 3, 1], vertical_alignment="center")
                    c_d1.markdown(f"**{encontrado.get('N_Cert', '')}**")
                    c_d2.write(encontrado.get("Fecha", ""))
                    c_d3.write(encontrado.get("Vendedor", ""))
                    c_d4.write(encontrado.get("Empresa_Emisora", encontrado.get("Emisor", "")))
                    
                    ruta = encontrado.get("Ruta_PDF")
                    if ruta and os.path.exists(ruta):
                        c_d5.markdown(f"<div style='text-align:center;'>{get_download_icon(ruta)}</div>", unsafe_allow_html=True)
                    else:
                        c_d5.markdown("<div style='text-align:center;'><span style='color:#EF4444; font-size:0.85rem;'>No disp.</span></div>", unsafe_allow_html=True)
                else:
                    st.error("❌ Los datos ingresados no coinciden con ningún certificado emitido. Verifique la información. Si el problema persiste, contacte con su vendedor para solicitar la emisión de su certificado.")
    
    st.write("")
    col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
    with col_back2:
        if st.button("Volver al Inicio", type="secondary", use_container_width=True):
            st.session_state.modo_vista = 'login'
            st.rerun()

# ==========================================
# 10. INTERFAZ PRINCIPAL (LOGIN Y NAVEGACIÓN)
# ==========================================
if not st.session_state.logueado:
    st.markdown("""
        <div class="top-navbar-bg"></div>
        <div class="navbar-logo">SICER <span>IA v9.1</span></div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('modo_vista', 'login') == 'login':
        st.write("")
        st.write("")
        
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("""
                <div style='text-align: center; margin-bottom: 30px;'>
                    <h1 style='color: #1E293B; font-weight: 900; font-style: italic; font-size: 3.5rem; letter-spacing: -1.5px; margin:0;'>
                        SICER <span style='background: linear-gradient(135deg, #4E008E 0%, #6A0DAD 100%); color: white; padding: 4px 15px; border-radius: 99px; font-size: 1.4rem; font-style: normal; vertical-align: middle; margin-left:10px;'>IA v9.1</span>
                    </h1>
                    <p style='color: #64748B; font-size: 1.1rem; margin-top: 10px; font-weight: 500;'>Sistema Inteligente de Certificados</p>
                </div>
            """, unsafe_allow_html=True)
        
            with st.container(border=True):
                st.markdown("""
                    <div style='display:flex; align-items:center; gap:10px; margin-bottom:20px;'>
                        <div style='background:#F3E8FF; padding:10px; border-radius:8px;'><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4E008E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div>
                        <h3 style='margin:0; color:#1E293B; font-size:1.3rem;'>Acceso de Personal</h3>
                    </div>
                """, unsafe_allow_html=True)
                with st.form("login_form", border=False, clear_on_submit=True):
                    usuario = st.text_input("Usuario")
                    clave = st.text_input("Contraseña", type="password")
                    st.write("")
                    submit_login = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
                    
                    if submit_login:
                        usuario_limpio = usuario.strip()
                        clave_limpia = clave.strip()
                        if usuario_limpio in st.session_state.usuarios and st.session_state.usuarios[usuario_limpio]["clave"] == clave_limpia:
                            st.session_state.logueado = True
                            st.session_state.rol = st.session_state.usuarios[usuario_limpio]["rol"]
                            st.session_state.usuario_actual = usuario_limpio
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas.")
            
            st.write("")
            
            with st.container(border=True):
                st.markdown("""
                    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
                        <div style='background:#ECFDF5; padding:10px; border-radius:8px;'><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><circle cx="10" cy="13" r="2"></circle><line x1="11.4" y1="14.4" x2="13.5" y2="16.5"></line></svg></div>
                        <h3 style='margin:0; color:#1E293B; font-size:1.3rem;'>Portal de Clientes</h3>
                    </div>
                    <p style='color:#64748B; font-size:0.95rem; margin-bottom: 20px;'>Área pública y segura para validar la autenticidad de sus compras y descargar los certificados de calidad oficiales emitidos por nuestras empresas.</p>
                """, unsafe_allow_html=True)
                if st.button("Verificar Certificado", type="primary", use_container_width=True):
                    st.session_state.modo_vista = 'verificar'
                    st.rerun()
    else:
        vista_verificacion_publica()

else:
    st.markdown("""
        <div class="top-navbar-bg"></div>
        <div class="navbar-logo">SICER <span>IA v9.1</span></div>
    """, unsafe_allow_html=True)
    
    st.markdown('<span class="logout-anchor"></span>', unsafe_allow_html=True)
    if st.button("Cerrar Sesión", type="secondary"):
        st.session_state.logueado = False
        st.session_state.modo_vista = 'login'
        st.rerun()

    if st.session_state.rol == "administrador":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Emisión", "Usuarios", "Historial", "Configuración y Diseño", "Motor IA"])
        with tab1: tab_emision()
        with tab2: tab_usuarios()
        with tab3: tab_historial_general()
        with tab4: tab_configuracion_diseno()
        with tab5: tab_ajustes_sistema()
            
    elif st.session_state.rol == "emisor":
        tab1, tab2 = st.tabs(["Emisión", "Historial"])
        with tab1: tab_emision()
        with tab2: tab_historial_general()

    elif st.session_state.rol == "vendedor":
        tab1, tab2 = st.tabs(["Solicitar Certificado", "Mis certificados"])
        with tab1: tab_solicitar_vendedor()
        with tab2: tab_historial_vendedor()
