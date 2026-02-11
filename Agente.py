import os
import json
import glob
import unicodedata
import datetime
import re
import uuid
import vertexai
from fpdf import FPDF
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=PROJECT_ID, location="us-central1")

class MaleonChatAgent:
    def __init__(self, storage_file="memoria_maleon.json", 
                 vip_file="data/contexto/invitados_vip.json",
                 knowledge_path="data/conocimiento/*.txt"):
        
        self.storage_file = storage_file
        self.vip_file = vip_file
        self.knowledge_path = knowledge_path
        os.makedirs("static/reportes", exist_ok=True)
        self.cargar_datos()

        self.system_instruction = (
            "Eres Maleón, asistente yucateco del IMET. Hablas con cortesía, usando 'bomba', 'nené', 'mare'. "
            "PROHIBIDO usar 'mira'.\n\n"
            "--- CONOCIMIENTO ---\n"
            f"{self.knowledge_text}\n"
            "--- REGLAS ---\n"
            "1. CERO MARKDOWN. 2. BREVEDAD (30-40 palabras). 3. PUNTO FINAL."
        )

        self.model = GenerativeModel("gemini-2.0-flash", system_instruction=self.system_instruction)
        self.history = self._load_memory()
        self.chat = self.model.start_chat(history=self.history)

    def cargar_datos(self):
        try:
            if os.path.exists(self.vip_file):
                with open(self.vip_file, 'r', encoding='utf-8') as f:
                    self.vip_data = json.load(f)
            else: self.vip_data = {}
        except: self.vip_data = {}

        self.knowledge_text = ""
        try:
            files = glob.glob(self.knowledge_path)
            for file_path in files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.knowledge_text += f"\n--- INFO {os.path.basename(file_path)} ---\n{f.read()}\n"
        except: pass

    def _normalizar(self, texto):
        return "".join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c)).lower()

    def detectar_vip(self, mensaje):
        msg_norm = self._normalizar(mensaje)
        for key, data in self.vip_data.items():
            for alias in data.get("alias", []):
                if f" {self._normalizar(alias)} " in f" {msg_norm} ": return data
        return None

    def _crear_pdf(self, titulo, contenido, incluir_grafico=False):
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # --- LOGOS INSTITUCIONALES (Cabecera) ---
            if os.path.exists("static/IMET_LOGO.png"):
                pdf.image("static/IMET_LOGO.png", x=10, y=8, w=30)
            if os.path.exists("static/TECHMALEON_LOGO.png"):
                pdf.image("static/TECHMALEON_LOGO.png", x=160, y=8, w=40)
            
            pdf.ln(20) # Espacio para los logos

            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, titulo.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='C')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(0, 10, f"Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='R')
            pdf.ln(5)

            pdf.set_font("Arial", size=11)
            contenido_limpio = contenido.replace("*", "").replace("#", "")
            pdf.multi_cell(0, 7, contenido_limpio.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(10)

            if incluir_grafico and os.path.exists("static/grafico_impacto_ssp.png"):
                pdf.add_page()
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "ANEXO VISUAL: IMPACTO ESTRATEGIA SSP", ln=True, align='C')
                pdf.image("static/grafico_impacto_ssp.png", x=10, w=190)
            
            nombre = f"reporte_{uuid.uuid4().hex[:8]}.pdf"
            ruta_pdf = f"static/reportes/{nombre}"
            pdf.output(ruta_pdf)
            return f"/static/reportes/{nombre}"
        except Exception as e:
            print(f"Error PDF: {e}")
            return None

    def answer(self, user_message, user_time=None):
        msg_lower = user_message.lower()
        
        # 1. Triggers de Reporte
        triggers = ['reporte', 'plan de', 'propuesta', 'documento', 'analisis', 'hazme un', 'genera un']
        es_reporte = any(f in msg_lower for f in triggers)

        if es_reporte and "mapa" not in msg_lower:
            if len(user_message.split()) < 3:
                return "¡Ay mare! Con gusto le ayudo, pero dígame ¿sobre qué tema en específico quiere que prepare el reporte, nené?"
            
            incluir_img = any(kw in msg_lower for kw in ['seguridad', 'ssp', 'impacto', 'policia'])
            
            # --- MODELO LIMPIO (SIN PERSONALIDAD) ---
            # Instanciamos un modelo fresco SOLO para esta tarea, sin reglas de Maleón
            analista_bot = GenerativeModel("gemini-2.0-flash")
            
            prompt_reporte = (
                "Eres un motor de análisis de texto objetivo.\n"
                f"TAREA: Analizar la siguiente base de conocimiento y redactar un informe sobre: {user_message}\n\n"
                "--- BASE DE CONOCIMIENTO (FUENTE ÚNICA) ---\n"
                f"{self.knowledge_text}\n\n"
                "--- INSTRUCCIONES ---\n"
                "1. Si la información no está en la base de conocimiento, usa tu conocimiento general para complementar pero prioriza los archivos.\n"
                "2. NO menciones que eres una IA o asistente.\n"
                "3. ESTRUCTURA: Diagnóstico, Estrategia, Conclusión.\n"
                "4. FORMATO: Texto plano (sin markdown), párrafos claros, tono formal.\n"
                "5. LONGITUD: Mínimo 400 palabras."
            )
            
            try:
                # Usamos generate_content directamente en el modelo limpio
                res = analista_bot.generate_content(prompt_reporte)
                
                # Validación estricta: Si se niega, forzamos un resumen genérico
                texto_final = res.text
                if not texto_final or "no puedo" in texto_final.lower():
                    texto_final = "No se encontró información específica en los archivos internos, pero aquí presento un análisis general basado en estándares del sector:\n\n" + \
                                  "1. Diagnóstico: Se requiere fortalecer la infraestructura tecnológica.\n" + \
                                  "2. Estrategia: Implementación de sistemas de vigilancia inteligente y capacitación.\n" + \
                                  "3. Conclusión: La modernización es clave para el desarrollo regional."

                ruta = self._crear_pdf(f"ANALISIS ESTRATEGICO: {user_message[:40].upper()}", texto_final, incluir_grafico=incluir_img)
                
                if ruta:
                    return f"Listo nené, ya terminé el análisis profundo sobre ese tema. Aquí tiene el documento para su revisión.<br><br><a href='{ruta}' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>📥 DESCARGAR REPORTE PDF</a>"
                else:
                    return "¡Ay fo! Hubo un problema al crear el archivo PDF."
            except Exception as e:
                print(f"Error Crítico en Reporte: {e}")
                return "¡Ay mare! Se me trabó el sistema al generar ese documento."

        # 2. Mapas
        if "mapa" in msg_lower:
            if any(k in msg_lower for k in ["seguridad", "ssp", "inteligencia"]):
                return "¡Claro! Aquí tiene el mapa de inteligencia de la SSP.<br><br><a href='/static/mapa_inteligencia_ssp.html' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>🔍 VER MAPA DE INTELIGENCIA</a>"
            if any(k in msg_lower for k in ["desabasto", "agua", "municipio"]):
                return "Mare, aquí tiene el mapa de desabasto de agua en los municipios.<br><br><a href='/static/mapa_desabasto_yucatan.html' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #17a2b8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>💧 VER MAPA DE DESABASTO</a>"

        # 3. Charla Normal
        vip = self.detectar_vip(user_message)
        ctx = f"\n[VIP: {vip['nombre']}]" if vip else ""
        if user_time: ctx += f" [Hora: {user_time}]"

        try:
            response = self.chat.send_message(f"{user_message}{ctx}")
            self._save_memory()
            return response.text
        except:
            return "¡Ay fo! Se me gastó la batería un momento, ¿me lo repites?"

    def handle(self, text, user_time=None): return self.answer(text, user_time)

    def _load_memory(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Content(role=m['role'], parts=[Part.from_text(m['content'])]) for m in data]
            except: pass
        return []

    def _save_memory(self):
        serializable_history = [{"role": c.role, "content": c.parts[0].text} for c in self.chat.history]
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_history, f, indent=4, ensure_ascii=False)