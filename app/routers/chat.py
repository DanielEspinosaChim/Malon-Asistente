import random
import re
from fastapi import APIRouter
from pydantic import BaseModel
from thefuzz import fuzz, process
from uuid import uuid4 
from app.agent.core import MaleonChatAgent

from app.services.tts_service import TTSService
from app.services.cache_service import CacheService
from app.services.inteligencia_service import InteligenciaService
from app.config import BLACKLIST


router = APIRouter()
sesiones_activas = {} 
PALABRAS_CONTEXTUALES = [
    "hablamos",
    "dijiste",
    "resumen",
    "recordar",
    "recuerdas",
    "antes",
    "me dijiste",
    "platicamos",
    "qué hemos",
    "de qué",
    "lo anterior"
]

def es_contextual(texto: str) -> bool:
    texto = texto.lower()
    return any(p in texto for p in PALABRAS_CONTEXTUALES)

tts_service = TTSService()
cache_service = CacheService()
intel_service = InteligenciaService()


class Msg(BaseModel):
    text: str
    time: str = None
    session_id: str



@router.post("/chat")
async def chat(msg: Msg):

    texto_input = msg.text.lower().strip()
    es_dinamico = any(word in texto_input for word in BLACKLIST)
    es_memoria = es_contextual(texto_input)


    sid = msg.session_id

    if sid not in sesiones_activas:
        sesiones_activas[sid] = MaleonChatAgent()

    bot_personal = sesiones_activas[sid]

    match_clave = None

    if not es_dinamico and cache_service.cache:
        mejor_match, score = process.extractOne(
            texto_input,
            cache_service.cache.keys(),
            scorer=fuzz.token_set_ratio
        )

        if score > 75:
            match_clave = mejor_match

    if match_clave:
        variantes = cache_service.get(match_clave)
        if len(variantes) >= 3:
            return random.choice(variantes)

    # --- Generar respuesta nueva ---
    respuesta = bot_personal.handle(msg.text)
    print(f"DEBUG: Respuesta del Agente: {respuesta}", flush=True)
    respuesta_texto = ""
    # --- Manejo de Inteligencia Especializada ---
    if isinstance(respuesta, dict) and respuesta.get("type") == "function_call":
        args = respuesta["args"]
        muni_sucio = args.get("muni", "") # Capturamos el nombre tal cual viene del chat
        
        # CASO A: CRECIMIENTO (CatBoost)
        if respuesta["name"] == "predecir_crecimiento":
            muni_real = intel_service.limpiar_municipio(muni_sucio, pilar="servicios") # Normalizamos
            pred = intel_service.model_growth.predict([args["codigo"], muni_real, args["v1"], args["v2"], args["v3"]])[0]
            
            # Guardamos el resultado LIMPIO para el reporte PDF
            bot_personal.registrar_resultado("crecimiento", f"Negocio {pred} en {muni_real}")
            respuesta_texto = f"Mare nene, ese negocio en {muni_real} pinta para ser {pred}."

        # CASO B: SERVICIOS
        elif respuesta["name"] == "buscar_servicios":
            muni_real = intel_service.limpiar_municipio(muni_sucio, pilar="servicios") # Normalizamos
            filtro = intel_service.df_servicios[intel_service.df_servicios['NOM_MUN'] == muni_real]
            
            if not filtro.empty:
                datos = filtro.iloc[0]
                info = f"Situación: {datos['CATEGORIA']} - Desabasto: {datos['INDICE_DESABASTO']}"
                bot_personal.registrar_resultado("servicios", info) # Se guarda para el reporte
                respuesta_texto = f"Mira nene, en {muni_real} la situación es {datos['CATEGORIA']}. Ya lo anoté."
            else:
                respuesta_texto = f"Mare nene, no encontré datos de servicios para {muni_real}."

        # CASO C: SEGURIDAD
        elif respuesta["name"] == "consultar_seguridad":
            muni_real = intel_service.limpiar_municipio(muni_sucio, pilar="seguridad") # Normalizamos
            filtro = intel_service.df_seguridad[intel_service.df_seguridad['NOM_MUN'] == muni_real]
            
            if not filtro.empty:
                datos = filtro.iloc[0]
                info = f"Riesgo: {datos['CATEGORIA_SEGURIDAD']} - Aislados: {int(datos['NEGOCIOS_AISLADOS'])}"
                bot_personal.registrar_resultado("seguridad", info) # Se guarda para el reporte
                respuesta_texto = f"Chequé lo de seguridad en {muni_real} y está {datos['CATEGORIA_SEGURIDAD']}."
            else:
                respuesta_texto = f"Fíjate que no tengo el reporte de seguridad de {muni_real} a la mano."
            
        # (Aquí puedes añadir después los de Seguridad y Servicios)
    else:
        # 3. Si es charla normal, sacamos el contenido del texto
        if isinstance(respuesta, dict):
            respuesta_texto = respuesta.get("content", "")
        else:
            respuesta_texto = respuesta

    texto_para_audio = re.sub(r'<[^>]+>', '', respuesta_texto)
    audio_url = tts_service.synthesize(texto_para_audio)

    nueva_resp = {
        "reply": respuesta_texto,
        "audio_url": audio_url
    }

    if not es_dinamico and not es_memoria:
        llave = match_clave if match_clave else texto_input
        cache_service.set(llave, nueva_resp)


    return nueva_resp
