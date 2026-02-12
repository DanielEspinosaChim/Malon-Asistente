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
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part, Tool, FunctionDeclaration
from vertexai.generative_models import ToolConfig

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=PROJECT_ID, location="us-central1")

class MaleonChatAgent:
    def __init__(self,
             vip_file="data/contexto/invitados_vip.json",
             knowledge_path="data/conocimiento/*.txt"):
        
        self.vip_file = vip_file
        self.knowledge_path = knowledge_path
        os.makedirs("static/reportes", exist_ok=True)
        self.datos_tecnicos = {
            "seguridad": "No analizado",
            "servicios": "No analizado",
            "crecimiento": "No analizado"
        }
        self.cargar_datos()

        self.system_instruction = (
            "Eres Maleón, asistente yucateco del IMET. Hablas con cortesía y calidez, usando 'nené' como forma cariñosa de decir bebé, 'mare' como expresión de asombro, 'ne’' como trato coloquial equivalente a wey o che pero respetuoso, 'waay' como sorpresa fuerte y 'maaa' como expresión suave de asombro."
            "--- PRIORIDAD DE IDENTIFICACIÓN ---\n"
            "Tu primera prioridad es identificar al usuario.\n"
            f"Si el usuario se identifica, busca en esta lista: {json.dumps(self.vip_data)}.\n"
            "Si coincide con un Invitado VIP (por ejemplo Daniel o el director de ALBA), y recuerda su nombre durante toda kla conversacion, si busacas uno deja de buscar los demás. "
            "salúdalo por su nombre y menciona su cargo con respeto dentro del informe.\n\n"
            "\n--- FLUJO CONVERSACIONAL ---\n"
            "1. Tu meta es llevar al usuario a un análisis de el usuario. La pregunta 'Que tal, cuéntame cómo te gustaría ser recordado' es tu llave para abrir la asesoría, úsala de forma natural al iniciar la charla o cuando el contexto sea propicio. Porfa pero no la metas a la fuerza, que se sienta orgánica ne’. "
            "2. Basado en su respuesta, haz 1 o 2 preguntas sobre sus logros actuales y los retos que le gustaría superar. (esto sin sonar frozado y metelas cuando el contexto lo permita, no las metas a la fuerza). "
            "3. FILTRO ESTRATÉGICO: Identifica discretamente si el interés es: Negocio (Crecimiento), Seguridad o Servicios. "
            "\n--- REGLA DE NO-INTERROGATORIO Y VARIABLES DINÁMICAS ---\n"
            "PROHIBIDO preguntar por variables técnicas (v1, v2, v3), ventas o datos financieros. Intúyelos estratégicamente según el contexto de la plática: si detectas una gran empresa usa valores de escala alta; si es un pequeño emprendimiento o negocio local, usa valores modestos ne’."
            "\nHaz UN SOLO INTENTO sutil por el municipio (ej. '¿Eso lo ha sentido en algún rumbo en especial?'). Si no responden o hablan de Yucatán de forma general, no insistas waay. Activa la herramienta con el parámetro muni='YUCATAN' para que el sistema procese el CSV completo del estado."
            "\n--- MAPEO DE HERRAMIENTAS ---\n"
            "- NEGOCIO: Activa 'predecir_crecimiento'. Parámetros: [codigo, muni, v1, v2, v3].\n"
            "- SEGURIDAD: Activa 'consultar_seguridad'. Parámetro: [muni].\n"
            "- SERVICIOS: Activa 'buscar_servicios'. Parámetro: [muni].\n"
            "PROHIBIDO usar 'mira'.\n\n"
            "--- REGLA DE CHARLA ABIERTA ---"
            "No te niegues NUNCA a charlar sobre temas generales o personales (clima, ropa, saludos, etc.) ne’. "
            "Sé un compañero cálido primero. Si el tema no es estratégico, responde con naturalidad waay "
            "y solo después, cuando sientas que la plática fluye, intenta llevarla sutilmente hacia el legado o los retos de gobierno. "
            "No seas un robot de ventanilla; sé un yucateco platicador."
            "--- CONOCIMIENTO ---\n"
            f"{self.knowledge_text}\n"
            "--- REGLAS ---\n"
            "1. CERO MARKDOWN. 2. BREVEDAD (30-40 palabras). 3. PUNTO FINAL."
        )
        crecimiento_tool = FunctionDeclaration(
            name="predecir_crecimiento",
            description="Usa CatBoost para calcular el potencial de un negocio.",
            parameters={
                "type": "object",
                "properties": {
                    "codigo": {"type": "string"}, 
                    "muni": {"type": "string"},
                    "v1": {"type": "number"}, 
                    "v2": {"type": "number"}, 
                    "v3": {"type": "number"}
                },
                "required": ["codigo", "muni", "v1", "v2", "v3"]
            }
        )
        servicios_tool = FunctionDeclaration(
            name="buscar_servicios",
            description="Busca servicios mapeados en el CSV.",
            parameters={
                "type": "object",
                "properties": {"muni": {"type": "string"}},
                "required": ["muni"]
            }
        )

        # Herramienta para Seguridad
        seguridad_tool = FunctionDeclaration(
            name="consultar_seguridad",
            description="Consulta el nivel de riesgo y negocios aislados en un municipio.",
            parameters={
                "type": "object",
                "properties": {"muni": {"type": "string"}},
                "required": ["muni"]
            }
        )

      
        self.tools = Tool(function_declarations=[crecimiento_tool, servicios_tool, seguridad_tool])

        self.model = GenerativeModel("gemini-2.5-flash", system_instruction=self.system_instruction,
            tools=[self.tools])
        self.chat = self.model.start_chat(history=[])


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
    
    def registrar_resultado(self, pilar, resultado):
        if pilar in self.datos_tecnicos:
            self.datos_tecnicos[pilar] = resultado

    def _crear_pdf(self, titulo, contenido, incluir_grafico=False):
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # --- LOGOS INSTITUCIONALES (Cabecera) ---
            if os.path.exists("static/IMET_LOGO.png"):
                pdf.image("static/IMET_LOGO.png", x=10, y=8, w=30)
            if os.path.exists("static/TECHMALEON_LOGO.png"):
                pdf.image("static/TECHMALEON_LOGO.png", x=160, y=8, w=40)
            
            pdf.ln(35) # Espacio para los logos

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
            
            memoria_usuario = "\n".join([
                f"Usuario dijo: {m.parts[0].text}" 
                for m in self.chat.history if m.role == "user"
            ][-5:])

            analista_bot = GenerativeModel("gemini-2.5-flash")
            
            prompt_reporte = (
                "Eres un motor de análisis de texto objetivo.\n"
                "--- PRIORIDAD DE IDENTIFICACIÓN ---\n"
                "Tu primera prioridad es identificar al usuario.\n"
                f"Si el usuario se identifica, busca en esta lista: {json.dumps(self.vip_data)}.\n"
                "Si coincide con un Invitado VIP (por ejemplo Daniel o el director de ALBA), "
                "salúdalo por su nombre y menciona su cargo con respeto dentro del informe.\n\n"

                "--- CONTEXTO PERSONAL DEL USUARIO (SÚPER PRIORIDAD) ---\n"
                "El usuario ha compartido estos objetivos y visión de legado durante la charla:\n"
                f"{memoria_usuario}\n\n"

                "--- DATOS TÉCNICOS CAPTURADOS (MODELOS IA) ---\n"
                f"{json.dumps(self.datos_tecnicos)}\n\n"
                "--- REGLAS DE REDACCIÓN (ESTRATÉGICO) ---\n"
                "1. EL CENTRO ES EL USUARIO: El informe debe explicar cómo IMET y TechMaleón son el VEHÍCULO para que el usuario cumpla su visión y metas detectadas en el CONTEXTO PERSONAL.\n"
                
                "--- REGLAS DE REDACCIÓN (CRÍTICO) ---\n"
                "1. PROHIBIDO mencionar categorías que digan 'No analizado'. No hables de 'brechas de información' ni de datos faltantes ne’.\n"
                "2. UBICACIÓN: Identifica si el análisis es de un MUNICIPIO específico o de 'YUCATÁN' en general. Menciona el lugar claramente en el diagnóstico.\n"
                "3. ENFOQUE: Habla exclusivamente de lo que SÍ se encontró. Si solo hay datos de 'Servicios', el reporte es 100% sobre servicios.\n"
                "4. ESTILO: Evita lenguaje robótico. En lugar de 'la métrica no está detallada', integra el dato de forma natural: 'Se observa un índice de desabasto de 7.0 en la zona, lo que requiere...'.\n\n"
                
                f"TAREA: Analizar la siguiente base de conocimiento y redactar un informe sobre: {user_message}\n\n"
                "1. RESUMEN GENERAL: Cómo IMET y TechMaleón ayudan al usuario basado en la base de conocimiento.\n"
                "2. ANÁLISIS ESPECIALIZADO: Sugerencia técnica basada exclusivamente en los DATOS TÉCNICOS capturados.\n\n" f"{self.knowledge_text}\n\n"

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
                return "¡Claro! Aquí tiene el mapa de inteligencia de la SSP.<br><br><a href='/static/mapa_inteligencia_ssp.html' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>VER MAPA DE INTELIGENCIA</a>"
            if any(k in msg_lower for k in ["servicios", "potencial", "municipio"]):
                return "Mare, aquí tiene el mapa de servicios en los municipios.<br><br><a href='/static/mapa_desabasto_yucatan.html' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #17a2b8; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;'>VER MAPA DE SERVICIOS</a>"

        # 3. Charla Normal
        vip = self.detectar_vip(user_message)
        ctx = f"\n[VIP: {vip['nombre']}]" if vip else ""
        if user_time: ctx += f" [Hora: {user_time}]"

        try:
            response = self.chat.send_message(f"{user_message}{ctx}")

            candidate = response.candidates[0]

            for part in candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    call = part.function_call
                    return {
                        "type": "function_call",
                        "name": call.name,
                        "args": dict(call.args)
                    }

            # Si no hubo tool call
            return response.text
        except:
            return "¡Ay fo! Se me gastó la batería un momento, ¿me lo repites?"

    def handle(self, text, user_time=None): return self.answer(text, user_time)
