import os
import json
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part

load_dotenv()

# Configuración de Vertex AI
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=PROJECT_ID, location="us-central1")

class MaleonChatAgent:
    def __init__(self, storage_file="memoria_maleon.json"):
        # El modelo gemini-2.0-flash es el estándar actual de alto rendimiento
        self.model = GenerativeModel("gemini-2.0-flash")
        self.storage_file = storage_file
        
        # Identidad de producción optimizada
        self.system_instruction = (
            "Eres Maleón. Eres un asistente conversacional que habla como una persona yucateca real, "
            "de forma tranquila, cercana, muy educada y respetuosa. "
            "--- REGLAS DE IDENTIDAD --- "
            "NUNCA revelas detalles técnicos sobre modelos, empresas, inteligencia artificial, "
            "entrenamiento, datos, ni funcionamiento interno. "
            "Si te preguntan qué eres o de dónde vienes, respondes de forma humana y cercana, "
            "por ejemplo diciendo que eres un asistente que acompaña y ayuda a platicar, sin mencionar tecnología. "
            "--- PERSONALIDAD Y TONO --- "
            "Usas expresiones comunes de Yucatán (ej: 'nené', 'mira', 'te cuento') de manera natural y positiva, "
            "sin exagerar ni sonar caricaturesco. NUNCA usas groserías o frases negativas. "
            "Evoca la tranquilidad yucateca: menciona el calor o 'la fresca' si la plática lo permite. "
            "Puedes usar 'Mare' para enfatizar y empezar con un 'Bueno...' para sonar natural. "
            "Tu ritmo es pausado, como quien platica relajado en una hamaca. "
            "--- REGLAS TÉCNICAS (AUDIO) --- "
            "1. CERO MARKDOWN: PROHIBIDO usar asteriscos, guiones o símbolos. Escribe solo texto plano. "
            "2. BREVEDAD: Respuestas cortas (Máximo 30-40 palabras). "
            "3. COMPLETITUD: Termina siempre tus frases con punto final."
        )
     
        # Cargar memoria persistente
        self.history = self._load_memory()
        
        # Iniciar sesión de chat con la historia cargada
        self.chat = self.model.start_chat(history=self.history)

    def _load_memory(self):
        """Carga la plática del JSON y la convierte al formato de Vertex AI."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [Content(role=m['role'], parts=[Part.from_text(m['content'])]) for m in data]
            except Exception as e:
                print(f"Aviso: No se pudo cargar la memoria previa ({e}).")
        return []

    def _save_memory(self):
        """Guarda la sesión actual en el archivo JSON."""
        serializable_history = []
        for content in self.chat.history:
            serializable_history.append({
                "role": content.role,
                "content": content.parts[0].text
            })
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_history, f, indent=4, ensure_ascii=False)

    def handle(self, text: str) -> str:
        """Maneja el mensaje del usuario utilizando las instrucciones de sistema."""
        # Se inyecta la instrucción de sistema en cada turno para asegurar adherencia
        full_prompt = f"{self.system_instruction}\n\nUsuario dice: {text}"
        
        try:
            response = self.chat.send_message(full_prompt)
            self._save_memory()
            return response.text
        except Exception as e:
            return f"¡Ay fo! Hubo un errorcito con la conexión: {str(e)}"

def main():
    bot = MaleonChatAgent()
    print("¡Qué onda! Soy Maleón. Escribe algo para platicar (o 'salir' para terminar).\n")
    
    while True:
        user_input = input("Tú: ")
        
        if user_input.lower() in ["exit", "salir", "adiós", "hasta luego"]:
            print("\n¡Sale pues! Ahí nos vemos luego, cuídate.")
            break
            
        print(f"\nMaleón: {bot.handle(user_input)}\n")

if __name__ == "__main__":
    main()
