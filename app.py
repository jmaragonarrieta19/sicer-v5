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
# 2. ICONOGRAFÍA Y DESCARGAS
# ==========================================
def get_download_icon(ruta):
    with open(ruta, "rb") as f:
        b64_pdf = base64.b64encode(f.read()).decode('utf-8')
    file_n = os.path.basename(ruta)
    return f'''
    <a href="data:application/pdf;base64,{b64_pdf}" download="{file_n}" title="Descargar Certificado"
       style="display: inline-flex; align-items: center; justify-content: center; background-color: #10B981; color: white; width: 34px; height: 34px; border-radius: 6px; text-decoration: none; transition: all 0.2s; box-shadow: 0 2px 4px rgba(16,185,129,0.2);">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
    </a>
    '''

def section_header(title, subtitle=""):
    st.markdown(f"""
        <div style="margin-top: 10px; margin-bottom: 25px; padding-bottom: 10px; border-bottom: 1px solid #E2E8F0;">
            <h2 style="margin: 0; font-size: 1.6rem; color: #1E293B; font-weight: 800; letter-spacing: -0.5px;">{title}</h2>
            {f'<p style="margin: 5px 0 0 0; color: #64748B; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. CONFIGURACIÓN DE PÁGINA Y CSS (KASNET STYLE)
# ==========================================
st.set_page_config(page_title="SICER IA v10.0", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    p, h1, h2, h3, h4, h5, h6, li, .stTextInput input, .stTextArea textarea, .stSelectbox div, label { 
        font-family: 'Inter', sans-serif !important; 
    }
    
    .stApp { background-color: #F8FAFC !important; } 
    header {display: none !important;} footer {display: none !important;}
    
    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 1200px; 
    }

    /* KASNET STYLE SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    /* RADIO BUTTONS COMO MENU LATERAL */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 12px 16px !important;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: #F1F5F9 !important;
    }
    /* Ocultar el círculo nativo del radio */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[data-baseweb="radio"] > div:first-child {
        display: none !important;
    }
    /* Estado Activo */
    [data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] {
        background-color: #EEF2FF !important; /* Fondo Morado Claro */
        border-left: 4px solid #4E008E !important; /* Línea de acento */
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[aria-checked="true"] p {
        color: #4E008E !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        color: #64748B;
        font-weight: 600;
        font-size: 1.05rem;
        margin-left: 5px;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important; 
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important; 
        padding: 2rem !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
        margin-bottom: 2rem !important;
    }
    
    /* INPUTS MODERNOS */
    .stTextInput label p, .stTextArea label p, .stSelectbox label p, .stFileUploader label p { 
        color: #1E293B !important; 
        font-weight: 700 !important; 
        font-size: 0.85rem !important; 
        margin-bottom: 6px !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 8px !important; 
        border: 1px solid #CBD5E1 !important;
        padding: 0.6rem 1rem !important; 
        background-color: #ffffff !important; 
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within { 
        border-color: #4E008E !important; 
        box-shadow: 0 0 0 2px rgba(78, 0, 142, 0.15) !important; 
    }
    
    /* BOTONES */
    button[kind="primary"], .stButton > button[kind="primary"] {
        background-color: #4E008E !important;
        border: none !important;
        color: #ffffff !important;
        border-radius: 8px !important; 
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        width: 100% !important; 
        min-height: 42px !important;
    }
    button[kind="primary"]:hover {
        background-color: #3B006A !important;
    }
    
    button[kind="secondary"], .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #CBD5E1 !important;
        color: #475569 !important;
        border-radius: 8px !important; 
        font-weight: 600 !important;
        width: 100% !important;
        min-height: 42px !important;
    }
    button[kind="secondary"]:hover { 
        background-color: #F1F5F9 !important; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. MOTOR HÍBRIDO SEGURO (SECRETOS + NUBE)
# ==========================================
ARCHIVO_CONFIG = "config_sicer.json"
ARCHIVO_HISTORIAL = "historial_sicer.json"
URL_FIREBASE = "https://sicer-ia-core-default-rtdb.firebaseio.com/" 
RUTA_LLAVE_FIREBASE = "firebase_key.json" 

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
                firebase_admin.initialize_app(cred, {'databaseURL': URL_FIREBASE})
                return True
            elif os.path.exists(RUTA_LLAVE_FIREBASE):
                cred = credentials.Certificate(RUTA_LLAVE_FIREBASE)
                firebase_admin.initialize_app(cred, {'databaseURL': URL_FIREBASE})
                return True
            else: return False
        except: return False
    return True

def cargar_configuracion():
    datos_nube = None
    if init_firebase():
        try: datos_nube = db.reference('config_db').get()
        except: pass
    if datos_nube:
        try:
            with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f: json.dump(datos_nube, f, ensure_ascii=False, indent=4)
        except: pass
        return datos_nube
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {
        "usuarios": {"admin": {"clave": "admin123", "rol": "administrador"}},
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
        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f: json.dump(datos, f, ensure_ascii=False, indent=4)
    except: pass
    if init_firebase():
        try: db.reference('config_db').set(datos)
        except: pass

def cargar_historial():
    datos_nube = None
    if init_firebase():
        try: datos_nube = db.reference('historial_db').get()
        except: pass
    if datos_nube:
        try:
            with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f: json.dump(datos_nube, f, ensure_ascii=False, indent=4)
        except: pass
        return datos_nube
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def guardar_historial(datos):
    try:
        with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f: json.dump(datos, f, ensure_ascii=False, indent=4)
    except: pass
    if init_firebase():
        try: db.reference('historial_db').set(datos)
        except: pass

# ==========================================
# 5. CARGA AL ESTADO DE LA SESIÓN
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

def obtener_imagen_html(ruta_imagen, altura_px=60):
    with open(ruta_imagen, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    return f'<div style="height: {altura_px}px; width: 100%; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;"><img src="data:image/png;base64,{encoded_string}" style="max-height: 100%; max-width: 100%; object-fit: contain;"></div>'

def limpiar_formulario_emision():
    st.session_state.datos_form = {"empresa": "", "ruc_emisor": "", "cliente": "", "ruc": "", "comprobante": "", "vendedor": "", "ciudad": "Jaén", "cantidad": "", "incluir_proteccion": True}
    st.session_state.ia_procesado = False
    st.session_state.uploader_key += 1

def es_comprobante_valido(comprobante):
    patron = r'^[FBE][A-Z0-9]{3}-\d+$'
    return bool(re.match(patron, comprobante.strip().upper()))

# ==========================================
# 6. MODALES Y FUNCIONES PDF
# ==========================================
@st.dialog("🚫 Rechazar Solicitud")
def modal_rechazar_solicitud(solicitud_id, comp_leido=""):
    motivo = st.text_area("Indique el motivo del rechazo:")
    c1, c2 = st.columns(2)
    if c1.button("Confirmar", type="primary", use_container_width=True):
        for idx, sol in enumerate(st.session_state.solicitudes):
            if sol['id'] == solicitud_id:
                st.session_state.solicitudes[idx]['estado'] = 'Rechazado'
                st.session_state.solicitudes[idx]['motivo_rechazo'] = motivo.strip()
                if comp_leido.strip(): st.session_state.solicitudes[idx]['comprobante'] = comp_leido.strip().upper()
        st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
        guardar_configuracion(st.session_state.config_db)
        limpiar_formulario_emision()
        st.rerun()
    if c2.button("Cancelar", use_container_width=True): st.rerun()

def render_texto_seguro(pdf, texto, align_code, font_name, font_size, line_height=5):
    pdf.set_font(font_name, '', font_size)
    texto_limpio = str(texto).replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<br>', '\n')
    pdf.multi_cell(0, line_height, texto_limpio, align=align_code)

def generar_pdf(empresa_emisora, ruc_emisor, cliente, ruc, comprobante, vendedor, ciudad, props_dinamicas, cantidad, carac_18, msg_final, num_cert, incluir_proteccion, texto_proteccion):
    pdf = FPDF()
    pdf.add_page()
    
    # ---------------------------------------------------------
    # ADOBE FIX: Marcas de agua seguras (Horizontales tipo Trama)
    # Evita el uso de self.rotate() manual que corrompe PyPDF
    # ---------------------------------------------------------
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(240, 240, 240) 
    marca_agua = f"CERTIFICADO {num_cert}     CERTIFICADO {num_cert}"
    for i in range(1, 10):
        pdf.text(x=10, y=i*30, txt=marca_agua)
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
        if os.path.exists(ruta_logo): pdf.ln(12)
        else: pdf.ln(25)
            
        ruta_plantilla = obtener_ruta_plantilla(empresa_emisora)
        usar_plantilla = os.path.exists(ruta_plantilla)
        
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
        
        texto_intro_formateado = st.session_state.mensaje_intro.format(cliente=cliente, tipo_doc=tipo_documento, num_doc=numero_limpio, comprobante=comprobante)
        texto_intro_completo = f"{empresa_emisora} CON RUC {ruc_emisor}, {texto_intro_formateado}"
        render_texto_seguro(pdf, texto_intro_completo, st.session_state.align_intro, "Arial", st.session_state.tamano_intro)
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
        
        if incluir_proteccion and texto_proteccion and texto_proteccion.strip() != "":
            pdf.set_font("Arial", 'B', 9)
            titulo_add = st.session_state.config_db.get("titulo_adicional", "PROTECCIÓN ADICIONAL").strip()
            pdf.cell(0, 6, f"1.{idx_num} {titulo_add.upper()}", ln=True)
            render_texto_seguro(pdf, texto_proteccion, "J", "Arial", 9)
            pdf.ln(4)
        
        texto_final_formateado = msg_final.format(empresa=empresa_emisora)
        render_texto_seguro(pdf, texto_final_formateado, st.session_state.align_final, "Arial", st.session_state.tamano_final)
        pdf.ln(8) 
        
        firmas_activas = st.session_state.config_db.get("firmas_config", {}).get(empresa_emisora, [])
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
        else:
            pdf.ln(15) 
            
        pdf.set_font("Arial", 'I', 8)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ciudad_final_pdf = ciudad if ciudad and str(ciudad).strip() != "" else "Jaén"
        pdf.cell(0, 6, f"{ciudad_final_pdf} - Certificado {num_cert} - Fecha: {fecha_actual}", ln=True, align='R')
        
        try:
            out = pdf.output(dest='S')
            if isinstance(out, str): pdf_bytes = out.encode('latin-1', 'ignore')
            else: pdf_bytes = bytes(out)
        except Exception:
            pdf_bytes = bytes(pdf.output())
            
        # ---------------------------------------------------------
        # ADOBE FIX: PyPDF Merge Seguro
        # ---------------------------------------------------------
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
                st.error(f"Error en plantilla PDF: {e}")
                
    finally:
        if os.path.exists(qr_path): os.remove(qr_path)
            
    return pdf_bytes

# ==========================================
# 7. MÓDULOS DE APLICACIÓN
# ==========================================

def tab_emision():
    section_header("Emisión de Certificados", "Extrae datos automáticamente de una boleta con IA o llena el formulario manualmente.")
    
    if st.session_state.rol == "administrador":
        empresas_permitidas_ui = [e["nombre"] for e in st.session_state.empresas]
    else:
        empresas_permitidas_ui = st.session_state.usuarios.get(st.session_state.usuario_actual, {}).get("empresas_permitidas", [])
        
    solicitudes_pendientes = [s for s in st.session_state.solicitudes if s['estado'] == 'Pendiente' and (st.session_state.rol == 'administrador' or s.get('empresa_destino') is None or s.get('empresa_destino') in empresas_permitidas_ui)]
    solicitud_seleccionada = None
    
    if solicitudes_pendientes:
        with st.expander(f"📥 Tienes {len(solicitudes_pendientes)} solicitudes pendientes", expanded=True):
            opciones = ["Seleccione una solicitud..."] + [f"Enviado por: {s['vendedor']} ({s['fecha'].split(' ')[0]}) ID: {s['id']}" for s in solicitudes_pendientes]
            sel = st.selectbox("Cargar solicitud para procesar:", opciones, label_visibility="collapsed")
            if sel != "Seleccione una solicitud...":
                id_sel = sel.split("ID: ")[1]
                solicitud_seleccionada = next((s for s in solicitudes_pendientes if s['id'] == id_sel), None)
    
    with st.container(border=True):
        col_ia1, col_ia2 = st.columns([5, 3], gap="large")
        imagen_a_procesar = None
        img_target = None
        
        with col_ia1: 
            if solicitud_seleccionada:
                st.info(f"Vendedor: **{solicitud_seleccionada['vendedor']}**")
                if os.path.exists(solicitud_seleccionada['ruta_imagen']):
                    img_target = Image.open(solicitud_seleccionada['ruta_imagen'])
                    imagen_a_procesar = img_target 
                    st.image(img_target, use_container_width=True)
            else:
                imagen_subida = st.file_uploader("Subir boleta o captura", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed", key=f"up_ia_{st.session_state.uploader_key}")
                if imagen_subida:
                    imagen_a_procesar = Image.open(imagen_subida)
                    img_target = imagen_a_procesar
                
        with col_ia2:
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
                                prompt = "Analiza la boleta: EMISOR, RUC_EMISOR, CLIENTE, RUC_DNI_CLIENTE, COMPROBANTE, VENDEDOR, CANTIDAD (calcula metros). FORMATO: EMISOR: X | RUC_EMISOR: X | CLIENTE: X | RUC_DNI_CLIENTE: X | COMPROBANTE: X | VENDEDOR: X | CANTIDAD: X"
                                respuesta = modelo_ia.generate_content([prompt, img_target])
                                texto = respuesta.text.strip().replace("*", "")
                                
                                datos = {}
                                partes = re.split(r'\s*\|\s*(?=[A-Z_]+:)', texto)
                                for p in partes:
                                    if ":" in p:
                                        k, v = p.split(":", 1)
                                        datos[k.strip()] = v.strip()
                                
                                extracted_ruc_clean = re.sub(r'[^0-9]', '', datos.get("RUC_EMISOR", ""))
                                allowed_rucs_clean = [re.sub(r'[^0-9]', '', str(e.get("ruc", ""))) for e in st.session_state.empresas if (st.session_state.rol == "administrador" or e["nombre"] in empresas_permitidas_ui)]
                                
                                if not extracted_ruc_clean or extracted_ruc_clean not in allowed_rucs_clean:
                                    st.session_state.ia_procesado = False
                                    modal_alerta_ruc(solicitud_seleccionada['id'] if solicitud_seleccionada else None, datos.get("COMPROBANTE", ""))
                                else:
                                    ciudad_final = "Jaén"
                                    for emp in st.session_state.empresas:
                                        if re.sub(r'[^0-9]', '', str(emp.get("ruc", ""))) == extracted_ruc_clean:
                                            ciudad_final = emp.get("direccion", "Jaén").split(",")[0].strip()
                                            break
                                    
                                    st.session_state.datos_form.update({
                                        "empresa": datos.get("EMISOR", ""), "ruc_emisor": datos.get("RUC_EMISOR", ""),
                                        "cliente": datos.get("CLIENTE", ""), "ruc": datos.get("RUC_DNI_CLIENTE", ""),
                                        "comprobante": datos.get("COMPROBANTE", ""), "vendedor": solicitud_seleccionada['vendedor'] if solicitud_seleccionada else datos.get("VENDEDOR", ""), 
                                        "ciudad": ciudad_final, "cantidad": datos.get("CANTIDAD", "")
                                    })
                                    st.session_state.ia_procesado = True
                                    st.session_state.uploader_key += 1
                                    st.rerun()
                            except: st.error("Error técnico con IA.")
                
                with c_btn_ia2:
                    if st.session_state.ia_procesado:
                        if st.button("Nuevo", type="secondary", use_container_width=True):
                            limpiar_formulario_emision()
                            st.rerun()
                            
            if solicitud_seleccionada:
                st.write("")
                if st.button("🚫 Rechazar Solicitud", type="secondary", use_container_width=True):
                    modal_rechazar_solicitud(solicitud_seleccionada['id'], st.session_state.datos_form.get("comprobante", ""))

    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B; margin-bottom:15px;'>Datos del Documento</p>", unsafe_allow_html=True)
        bloquear_campos = (st.session_state.rol == "emisor")
        uk = st.session_state.uploader_key
        
        c_r1_1, c_r1_2 = st.columns([6, 4], gap="medium")
        st.session_state.datos_form["empresa"] = c_r1_1.text_input("Empresa Emisora", value=st.session_state.datos_form.get("empresa", ""), disabled=bloquear_campos, key=f"e_in_{uk}")
        st.session_state.datos_form["ruc_emisor"] = c_r1_2.text_input("RUC Emisor", value=st.session_state.datos_form.get("ruc_emisor", ""), disabled=bloquear_campos, key=f"re_in_{uk}")

        c_r2_1, c_r2_2, c_r2_3, c_r2_4, c_r2_5 = st.columns([3, 2, 2, 2, 2], gap="medium")
        st.session_state.datos_form["cliente"] = c_r2_1.text_input("Cliente", value=st.session_state.datos_form.get("cliente", ""), disabled=bloquear_campos, key=f"c_in_{uk}")
        st.session_state.datos_form["ruc"] = c_r2_2.text_input("RUC/DNI", value=st.session_state.datos_form.get("ruc", ""), disabled=bloquear_campos, key=f"r_in_{uk}") 
        st.session_state.datos_form["comprobante"] = c_r2_3.text_input("N° Comprobante", value=st.session_state.datos_form.get("comprobante", ""), disabled=bloquear_campos, key=f"co_in_{uk}")
        st.session_state.datos_form["vendedor"] = c_r2_4.text_input("Vendedor", value=st.session_state.datos_form.get("vendedor", ""), disabled=bloquear_campos, key=f"v_in_{uk}")
        st.session_state.datos_form["ciudad"] = c_r2_5.text_input("Ciudad", value=st.session_state.datos_form.get("ciudad", "Jaén"), disabled=True, key=f"ci_in_{uk}")
        
        st.session_state.datos_form["cantidad"] = st.text_area("Detalle de Productos", value=st.session_state.datos_form.get("cantidad", ""), height=100, key=f"ca_in_{uk}")
        st.session_state.datos_form["incluir_proteccion"] = st.checkbox("Incluir cláusula de Protección Adicional", value=st.session_state.datos_form.get("incluir_proteccion", True), key=f"prot_check_{uk}")
        
        st.write("")
        campos_llenos = len(st.session_state.datos_form["empresa"].strip()) > 0 and len(st.session_state.datos_form["cliente"].strip()) > 0
        col_gen, col_dl = st.columns(2, gap="medium")
        
        with col_gen:
            if st.button("Generar Certificado", type="primary", disabled=not campos_llenos, use_container_width=True):
                comp_act = st.session_state.datos_form["comprobante"].strip()
                if not es_comprobante_valido(comp_act): st.error("❌ Formato de comprobante inválido.")
                elif any(c.get("Comprobante", "").strip().upper() == comp_act.upper() for c in st.session_state.historial_db): st.error("⚠️ Comprobante duplicado.")
                else:
                    num_certificado = datetime.now().strftime("%Y%m%d%H%M%S")
                    with st.spinner("Construyendo documento..."):
                        pdf_bytes = generar_pdf(
                            st.session_state.datos_form["empresa"], st.session_state.datos_form["ruc_emisor"], 
                            st.session_state.datos_form["cliente"], st.session_state.datos_form["ruc"], 
                            comp_act.upper(), st.session_state.datos_form["vendedor"], st.session_state.datos_form["ciudad"], 
                            st.session_state.propiedades_dinamicas, st.session_state.datos_form["cantidad"], 
                            st.session_state.caracteristicas_18, st.session_state.mensaje_final, num_certificado, 
                            st.session_state.datos_form["incluir_proteccion"], st.session_state.config_db.get("texto_adicional", "")
                        )
                        pdf_filepath = os.path.join("certificados_emitidos", f"Certificado_{num_certificado}.pdf")
                        with open(pdf_filepath, "wb") as f: f.write(pdf_bytes)
                        
                        st.session_state.historial_db.append({
                            "N_Cert": num_certificado, "Fecha": datetime.now().strftime("%d/%m/%Y"),
                            "Empresa_Emisora": st.session_state.datos_form["empresa"], "Usuario_Emisor": st.session_state.usuario_actual,
                            "Cliente": st.session_state.datos_form["cliente"], "Documento": st.session_state.datos_form["ruc"], 
                            "Comprobante": comp_act.upper(), "Vendedor": st.session_state.datos_form["vendedor"], 
                            "Estado": "Emitido", "Ruta_PDF": pdf_filepath
                        })
                        guardar_historial(st.session_state.historial_db)
                        
                        if solicitud_seleccionada:
                            for idx, sol in enumerate(st.session_state.solicitudes):
                                if sol['id'] == solicitud_seleccionada['id']: st.session_state.solicitudes[idx]['estado'] = 'Completado'
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
                    st.markdown(f'''<a href="data:application/pdf;base64,{b64_pdf}" download="{os.path.basename(st.session_state.ultimo_pdf_ruta)}" style="display: flex; align-items: center; justify-content: center; gap: 10px; background: #10B981; color: white; padding: 0.6rem 1.5rem; border-radius: 8px; text-decoration: none; font-weight: 600;">DESCARGAR PDF</a>''', unsafe_allow_html=True)

def tab_configuracion_diseno():
    section_header("Configuración Visual", "Catálogo, logos, fondos en PDF y firmas de la empresa.")
    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B;'>Añadir Empresa</p>", unsafe_allow_html=True)
        with st.form("form_add_emp", clear_on_submit=True):
            c_cat1, c_cat2, c_cat3 = st.columns([1, 1, 1], gap="medium")
            nueva_empresa = c_cat1.text_input("Razón Social")
            nuevo_ruc = c_cat2.text_input("RUC")
            nueva_dir = c_cat3.text_input("Dirección (Ciudad)")
            if st.form_submit_button("Añadir", type="primary", use_container_width=True):
                if nueva_empresa.strip() and nuevo_ruc.strip():
                    st.session_state.empresas.append({"nombre": nueva_empresa.upper(), "ruc": nuevo_ruc.strip(), "direccion": nueva_dir})
                    st.session_state.config_db["empresas"] = st.session_state.empresas
                    guardar_configuracion(st.session_state.config_db)
                    st.rerun()

    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B;'>Directorio</p>", unsafe_allow_html=True)
        for emp in list(st.session_state.empresas):
            c_e1, c_e2, c_e3, c_e4 = st.columns([4, 2, 3, 1], vertical_alignment="center")
            c_e1.write(f"**{emp['nombre']}**")
            c_e2.write(f"RUC: {emp.get('ruc', '')}")
            c_e3.write(emp.get('direccion', ''))
            if len(st.session_state.empresas) > 1:
                # KASNET STYLE TRASH BUTTON
                if c_e4.button("🗑️", key=f"del_emp_{emp['nombre']}", help="Eliminar", use_container_width=True):
                    st.session_state.empresas = [e for e in st.session_state.empresas if e['nombre'] != emp['nombre']]
                    st.session_state.config_db["empresas"] = st.session_state.empresas
                    guardar_configuracion(st.session_state.config_db)
                    st.rerun()
            st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

    with st.container(border=True):
        nombres_empresas = [e["nombre"] for e in st.session_state.empresas]
        emp_visual = st.selectbox("Seleccione empresa a configurar:", nombres_empresas)
        if emp_visual:
            st.write("")
            c_img1, c_img2 = st.columns([1, 1], gap="large")
            with c_img1:
                st.markdown("<p style='font-weight:700; font-size:0.85rem;'>LOGO</p>", unsafe_allow_html=True)
                ruta_l = obtener_ruta_logo(emp_visual)
                if os.path.exists(ruta_l):
                    st.markdown(obtener_imagen_html(ruta_l, 60), unsafe_allow_html=True)
                    if st.button("🗑️ Quitar Logo", key="dl_btn", use_container_width=True): os.remove(ruta_l); st.rerun()
                else:
                    file_l = st.file_uploader("Subir logo", type=["png", "jpg"], label_visibility="collapsed")
                    if file_l and st.button("Guardar Logo", type="primary", use_container_width=True):
                        with open(ruta_l, "wb") as f: f.write(file_l.getbuffer())
                        st.rerun()
                        
            with c_img2:
                st.markdown("<p style='font-weight:700; font-size:0.85rem;'>PLANTILLA (.PDF)</p>", unsafe_allow_html=True)
                ruta_p = obtener_ruta_plantilla(emp_visual)
                if os.path.exists(ruta_p):
                    st.markdown('''<div style="height: 60px; display: flex; align-items: center; justify-content: center; border: 2px solid #10B981; border-radius: 8px; margin-bottom: 10px; background-color: #ECFDF5;"><span style="color: #10B981; font-weight: bold;">✓ Plantilla PDF Activa</span></div>''', unsafe_allow_html=True)
                    if st.button("🗑️ Quitar PDF", key="dp_btn", use_container_width=True): os.remove(ruta_p); st.rerun()
                else:
                    file_p = st.file_uploader("Subir diseño en .PDF", type=["pdf"], label_visibility="collapsed")
                    if file_p and st.button("Guardar Plantilla", type="primary", use_container_width=True):
                        with open(ruta_p, "wb") as f: f.write(file_p.getbuffer())
                        st.rerun()
                        
            st.markdown("<hr style='margin: 25px 0;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:700;'>Firmas Autorizadas</p>", unsafe_allow_html=True)
            
            firmas_emp = st.session_state.config_db.get("firmas_config", {}).get(emp_visual, [])
            with st.form(f"form_add_firma_{emp_visual}", clear_on_submit=True):
                c_f_add1, c_f_add2, c_f_add3 = st.columns([2, 2, 1], vertical_alignment="bottom")
                new_f_file = c_f_add1.file_uploader("Sube firma", type=["png", "jpg"], label_visibility="collapsed")
                new_f_cargo = c_f_add2.text_input("Cargo", placeholder="GERENTE GENERAL", label_visibility="collapsed")
                if c_f_add3.form_submit_button("Guardar", type="primary", use_container_width=True):
                    if new_f_file and new_f_cargo.strip():
                        f_id = uuid.uuid4().hex[:8]
                        with open(os.path.join(os.getcwd(), f"firma_{limpiar_nombre(emp_visual)}_{f_id}.png"), "wb") as f: f.write(new_f_file.getbuffer())
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
                        if os.path.exists(f_path): st.markdown(obtener_imagen_html(f_path, 40), unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align:center; font-size:0.8rem; font-weight:700;'>{f_data['cargo'].upper()}</div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_f_{f_data['id']}", help="Eliminar", use_container_width=True):
                            if os.path.exists(f_path): os.remove(f_path)
                            firmas_emp.remove(f_data)
                            st.session_state.config_db.setdefault("firmas_config", {})[emp_visual] = firmas_emp
                            guardar_configuracion(st.session_state.config_db)
                            st.rerun()

def tab_usuarios():
    section_header("Gestión de Personal")
    todas_empresas_nombres = [e["nombre"] for e in st.session_state.empresas]
    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B;'>Nuevo Usuario</p>", unsafe_allow_html=True)
        with st.form("form_users", clear_on_submit=True):
            c_u1, c_u2, c_u3 = st.columns([1, 1, 1])
            n_usr = c_u1.text_input("Usuario")
            n_pass = c_u2.text_input("Contraseña", type="password")
            n_rol = c_u3.selectbox("Rol", ["administrador", "emisor", "vendedor"])
            n_empresas = st.multiselect("Sedes Permitidas", todas_empresas_nombres, default=todas_empresas_nombres)
            if st.form_submit_button("Guardar Usuario", type="primary"):
                st.session_state.usuarios[n_usr.strip()] = {"clave": n_pass.strip(), "rol": n_rol, "empresas_permitidas": n_empresas}
                st.session_state.config_db["usuarios"] = st.session_state.usuarios
                guardar_configuracion(st.session_state.config_db)
                st.rerun()
                
    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B;'>Directorio Activo</p>", unsafe_allow_html=True)
        for u, dat in list(st.session_state.usuarios.items()):
            if u == "cliente_acceso": continue
            c_r1, c_r2, c_r3, c_r4, c_r5 = st.columns([2, 2, 3, 1, 1], vertical_alignment="center")
            c_r1.write(f"**{u}**")
            c_r2.write(dat['rol'].capitalize())
            c_r3.write(f"{len(dat.get('empresas_permitidas', []))} asignadas")
            if c_r4.button("Ver", key=f"btn_ver_{u}"): modal_verificar_clave(u)
            if u != st.session_state.usuario_actual:
                if c_r5.button("🗑️", key=f"btn_del_{u}", help="Eliminar usuario"): modal_confirmar_eliminacion(u)
            st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)

def tab_historial_general():
    section_header("Auditoría de Documentos")
    emisor_empresas = st.session_state.usuarios.get(st.session_state.usuario_actual, {}).get("empresas_permitidas", [])
    emisor_empresas_norm = [str(e).upper().replace(' ','') for e in emisor_empresas]
    
    if st.session_state.rol == "administrador": historial_filtrado = st.session_state.historial_db
    else: historial_filtrado = [c for c in st.session_state.historial_db if str(c.get("Empresa_Emisora", "")).upper().replace(' ','') in emisor_empresas_norm]

    with st.container(border=True):
        st.markdown("<p style='font-weight:700; color:#1E293B;'>Certificados Emitidos</p>", unsafe_allow_html=True)
        if len(historial_filtrado) > 0:
            is_admin = (st.session_state.rol == "administrador")
            if is_admin: c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 2.5, 2, 2, 1.5, 1.5, 1, 1])
            else: c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2.5, 2, 2, 1.5, 1.5, 1])
                
            c1.markdown("**FECHA**")
            c2.markdown("**EMPRESA**")
            c3.markdown("**COMPROBANTE**")
            c4.markdown("**CLIENTE**")
            c5.markdown("**VENDEDOR**")
            c6.markdown("**EMISOR**")
            c7.markdown("**DOC**")
            if is_admin: c8.markdown("**ACC**")
            st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
            
            for cert in reversed(historial_filtrado):
                if is_admin: c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 2.5, 2, 2, 1.5, 1.5, 1, 1], vertical_alignment="center")
                else: c1, c2, c3, c4, c5, c6, c7 = st.columns([1.5, 2.5, 2, 2, 1.5, 1.5, 1], vertical_alignment="center")
                    
                c1.write(cert["Fecha"])
                c2.write(cert.get("Empresa_Emisora", cert.get("Emisor", "")))
                c3.write(cert["Comprobante"])
                c4.write(cert["Cliente"])
                c5.write(cert.get("Vendedor", ""))
                c6.write(cert.get("Usuario_Emisor", "Admin")) 
                
                ruta = cert.get("Ruta_PDF")
                if ruta and os.path.exists(ruta): c7.markdown(get_download_icon(ruta), unsafe_allow_html=True)
                
                if is_admin:
                    if c8.button("🗑️", key=f"del_cert_{cert['N_Cert']}", help="Eliminar certificado"):
                        st.session_state.historial_db = [c for c in st.session_state.historial_db if c['N_Cert'] != cert['N_Cert']]
                        guardar_historial(st.session_state.historial_db)
                        if ruta and os.path.exists(ruta):
                            try: os.remove(ruta)
                            except: pass
                        st.rerun()
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        else: st.info("No hay certificados en esta sede.")

def tab_solicitar_vendedor():
    section_header("Solicitar Certificado")
    with st.container(border=True):
        with st.form("form_solicitud", clear_on_submit=True):
            foto = st.file_uploader("Captura de la boleta (Obligatorio)", type=["png", "jpg", "jpeg", "webp"])
            if st.form_submit_button("Enviar Solicitud", type="primary"):
                if foto is None: st.error("⚠️ Sube la imagen.")
                else:
                    f_path = os.path.join("solicitudes_img", f"req_{uuid.uuid4().hex[:8]}.png")
                    with open(f_path, "wb") as f: f.write(foto.getbuffer())
                    st.session_state.solicitudes.append({
                        "id": uuid.uuid4().hex[:8], "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "vendedor": st.session_state.usuario_actual, "empresas_vendedor": st.session_state.usuarios[st.session_state.usuario_actual].get("empresas_permitidas", []),
                        "comprobante": "Por escanear", "ruta_imagen": f_path, "estado": "Pendiente"
                    })
                    st.session_state.config_db['solicitudes'] = st.session_state.solicitudes
                    guardar_configuracion(st.session_state.config_db)
                    st.success("✅ Solicitud enviada.")
                    st.rerun()

def tab_historial_vendedor():
    section_header("Mis Certificados")
    with st.container(border=True):
        mis_certificados = [c for c in st.session_state.historial_db if c.get("Vendedor") == st.session_state.usuario_actual]
        if mis_certificados:
            c1, c2, c3, c4 = st.columns([2, 3, 4, 1])
            c1.markdown("**FECHA**")
            c2.markdown("**COMPROBANTE**")
            c3.markdown("**CLIENTE**")
            c4.markdown("**DOC.**")
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            for cert in reversed(mis_certificados):
                c1, c2, c3, c4 = st.columns([2, 3, 4, 1], vertical_alignment="center")
                c1.write(cert["Fecha"])
                c2.write(cert["Comprobante"])
                c3.write(cert["Cliente"])
                ruta = cert.get("Ruta_PDF")
                if ruta and os.path.exists(ruta): c4.markdown(get_download_icon(ruta), unsafe_allow_html=True)
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
        else: st.info("No tienes certificados.")

def vista_verificacion_publica():
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 40px;'>
            <h2 style='color: #1E293B; font-weight: 800;'>Verificación de Certificados</h2>
            <p style='color: #64748B;'>Ingrese los datos exactos de su comprobante para buscar y descargar su certificado.</p>
        </div>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        with st.form("form_verificacion", border=False):
            c1, c2, c3 = st.columns(3, gap="medium")
            empresa_verif = c1.selectbox("Empresa Emisora", [e["nombre"] for e in st.session_state.empresas])
            comp_verif = c2.text_input("N° Comprobante")
            doc_verif = c3.text_input("RUC / DNI")
            if st.form_submit_button("Buscar Certificado", type="primary"):
                comp_in = re.sub(r'\s+', '', re.sub(r'[.,\-_/]', ' ', str(comp_verif).upper()))
                encontrado = next((c for c in st.session_state.historial_db if re.sub(r'\s+', '', re.sub(r'[.,\-_/]', ' ', str(c.get("Comprobante", "")).upper())) == comp_in and re.sub(r'[^0-9]', '', str(c.get("Documento", ""))) == re.sub(r'[^0-9]', '', str(doc_verif))), None)
                if encontrado:
                    st.success("✅ ¡Certificado validado!")
                    c_d1, c_d2 = st.columns([8, 2], vertical_alignment="center")
                    c_d1.write(f"**Certificado:** {encontrado.get('N_Cert', '')} | **Fecha:** {encontrado.get('Fecha', '')} | **Empresa:** {encontrado.get('Empresa_Emisora', '')}")
                    ruta = encontrado.get("Ruta_PDF")
                    if ruta and os.path.exists(ruta): c_d2.markdown(get_download_icon(ruta), unsafe_allow_html=True)
                else: st.error("❌ No se encontró el certificado.")

# ==========================================
# 8. RUTEADOR Y MENÚ LATERAL (SIDEBAR)
# ==========================================
if not st.session_state.logueado:
    st.markdown('<div class="top-navbar-bg"></div><div class="navbar-logo">SICER <span>IA v10.0</span></div>', unsafe_allow_html=True)
    if st.session_state.get('modo_vista', 'login') == 'login':
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<h1 style='text-align:center; font-style:italic; font-weight:900;'>SICER IA</h1>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h3 style='margin:0;'>Acceso</h3>", unsafe_allow_html=True)
                with st.form("login_form", border=False):
                    usuario = st.text_input("Usuario")
                    clave = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Ingresar", type="primary"):
                        if usuario.strip() in st.session_state.usuarios and st.session_state.usuarios[usuario.strip()]["clave"] == clave.strip():
                            st.session_state.logueado, st.session_state.rol, st.session_state.usuario_actual = True, st.session_state.usuarios[usuario.strip()]["rol"], usuario.strip()
                            st.rerun()
                        else: st.error("❌ Credenciales incorrectas.")
            if st.button("Verificar Certificado (Público)"):
                st.session_state.modo_vista = 'verificar'
                st.rerun()
    else: vista_verificacion_publica()

else:
    # --- MENÚ LATERAL TIPO KASNET ---
    if st.session_state.rol == "administrador": menu = ["🏠 Inicio", "👥 Usuarios", "🕒 Transacciones", "⚙️ Configuración", "🧠 Motor IA"]
    elif st.session_state.rol == "emisor": menu = ["🏠 Inicio", "🕒 Transacciones"]
    else: menu = ["📄 Solicitar Certificado", "📦 Mis Operaciones"]

    with st.sidebar:
        st.markdown(f"""
            <div style="padding: 10px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;">
                <div style="display:flex; align-items:center; gap: 12px;">
                    <div style="width: 45px; height: 45px; border-radius: 50%; background-color: #4E008E; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">
                        {st.session_state.usuario_actual[0].upper()}
                    </div>
                    <div>
                        <h4 style="margin:0; color:#1E293B; font-weight:800; font-size: 1.1rem; line-height:1.2;">{st.session_state.usuario_actual.upper()}</h4>
                        <p style="margin:0; font-size:0.8rem; color:#10B981; font-weight:700;">Agente Digital</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        seleccion = st.radio("Navegación", menu, label_visibility="collapsed")
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logueado = False
            st.rerun()

    # --- RUTAS DE NAVEGACIÓN ---
    if seleccion == "🏠 Inicio": tab_emision()
    elif seleccion == "👥 Usuarios": tab_usuarios()
    elif seleccion == "🕒 Transacciones": tab_historial_general()
    elif seleccion == "⚙️ Configuración": tab_configuracion_diseno()
    elif seleccion == "🧠 Motor IA": tab_ajustes_sistema()
    elif seleccion == "📄 Solicitar Certificado": tab_solicitar_vendedor()
    elif seleccion == "📦 Mis Operaciones": tab_historial_vendedor()