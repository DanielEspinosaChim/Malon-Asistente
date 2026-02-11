import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

# Forzamos los datos que ya confirmamos
project_id = "maleon" # Tu proyecto de la imagen
location = "us-central1"

vertexai.init(project=project_id, location=location)

# Usamos la versión más nueva de 2026
model = GenerativeModel("gemini-2.5-flash")

try:
    print("--- Contactando a Maleón... ---")
    response = model.generate_content("¿Qué onda Maleón? ¿Ya estás conectado?")
    print(f"\n✅ RESPUESTA EXITOSA: {response.text}")
except Exception as e:
    print(f"\n❌ ERROR TODAVÍA: {e}")