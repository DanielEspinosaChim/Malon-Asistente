import os
import uuid
import json
import random
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.cloud import texttospeech
from thefuzz import fuzz, process
from dotenv import load_dotenv

load_dotenv()

from Agente import MaleonChatAgent

app = FastAPI()
bot = MaleonChatAgent()

# Configuramos el cliente con el proyecto de cuota explícito
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "maleon")
client = texttospeech.TextToSpeechClient(
    client_options={"quota_project_id": PROJECT_ID}
)

CACHE_FILE = "cache_inteligente.json"
BLACKLIST = ["clima", "tiempo", "hora", "hoy", "ayer", "mañana"]

def cargar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def guardar_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

cache_memoria = cargar_cache()

os.makedirs("temp_audio", exist_ok=True)
app.mount("/avatar", StaticFiles(directory="avatar"), name="avatar")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp_audio", StaticFiles(directory="temp_audio"), name="temp_audio")

class Msg(BaseModel):
    text: str
    time: str = None # Añadimos el campo opcional de hora

@app.post("/chat")
async def chat(msg: Msg):
    global cache_memoria
    texto_input = msg.text.lower().strip()
    
    try:
        es_dinamico = any(word in texto_input for word in BLACKLIST)
        
        # 1. BUSCAR EN EL CACHÉ (Más flexible: bajamos a 75% de similitud)
        match_clave = None
        if not es_dinamico and cache_memoria:
            # Usamos token_set_ratio que es mejor para frases con palabras movidas o typos
            mejor_match, score = process.extractOne(texto_input, cache_memoria.keys(), scorer=fuzz.token_set_ratio)
            
            if score > 75: 
                match_clave = mejor_match
                print(f">>> Match detectado ({score}%): {match_clave}")

        # 2. LA TRAMPA: Si ya tenemos variantes para esta idea, elige una
        if match_clave:
            variantes = cache_memoria[match_clave]
            # Si ya tenemos al menos 3 respuestas guardadas para esta frase, 
            # ya no gastamos en la API, solo regresamos una al azar.
            if len(variantes) >= 3:
                print(">>> Usando trampa: Respuesta aleatoria del caché.")
                return random.choice(variantes)
            
            # Si tenemos menos de 3, a veces queremos generar una nueva 
            # para alimentar la variedad del caché (50% de probabilidad)
            if random.random() > 0.5:
                print(">>> Match encontrado, pero generando variante nueva para el futuro.")
            else:
                return random.choice(variantes)

        # 3. GENERAR RESPUESTA NUEVA (Gemini + TTS)
        respuesta_texto = bot.handle(msg.text, user_time=msg.time)
        
        # Síntesis de Google Cloud (La voz que calibramos)
        synthesis_input = texttospeech.SynthesisInput(text=respuesta_texto)
        voice = texttospeech.VoiceSelectionParams(language_code="es-US", name="es-US-Neural2-B")
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=-4.0, 
            speaking_rate=0.85
        )
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join("temp_audio", filename)
        with open(filepath, "wb") as out:
            out.write(response.audio_content)

        nueva_resp = {"reply": respuesta_texto, "audio_url": f"/temp_audio/{filename}"}

        # 4. GUARDADO INTELIGENTE: Agrupar bajo la llave del match si existía
        llave_a_usar = match_clave if match_clave else texto_input
        
        if llave_a_usar in cache_memoria:
            cache_memoria[llave_a_usar].append(nueva_resp)
        else:
            cache_memoria[llave_a_usar] = [nueva_resp]
        
        guardar_cache(cache_memoria)
        return nueva_resp

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Fallo en la matriz.")

@app.get("/")
async def index():
    return FileResponse("static/index.html")
