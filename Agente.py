import requests #se usa para enviar la peticion al endpoint
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
#humanMessage representa el mensaje el usuario
#AIMessage representa los mensaje generacion por el modelo

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY or API_KEY.startswith("PEGA_"):
    raise RuntimeError("Falta GROQ_API_KEY en el archivo .env")

class GroqChat:
    def __init__(self, model="llama-3.1-8b-instant"):
        self.api_key = API_KEY
        self.model = model
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization":f"Bearer {self.api_key}",
            "Content-Type":"application/json"
        }
    def _normalize(self, messages):
        normalized = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                normalized.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, HumanMessage):
                normalized.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                normalized.append({
                    "role": "assistant",
                    "content": msg.content
                })
        return normalized
        
    
    def _call(self, input_messages):
        msgs = self._normalize(input_messages)
        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.8,
            "max_tokens": 400  
        }
        r = requests.post(
            self.url,
            json=payload,
            headers=self.headers
        )
        try:
            data=r.json()
        except Exception:
            return "Error no estas pasando un puto Json pendejo estupido"
        if "choices" not in data:
            return f"Errer: respuesta inesperada {data}" 
        return data["choices"][0]["message"]["content"]
    def invoke(self, input, config=None):
        return self._call(input)



class MaleonChatAgent:
    def __init__(self):
        self.llm = GroqChat()

        # System prompt: identidad + tono yucateco
        self.chat_history = [
            SystemMessage(
                content=(
                    "Eres Maleón. Eres un asistente conversacional que habla como una persona yucateca real, "
                    "de forma tranquila, cercana, muy educada y respetuosa. "
                    # --- REGLAS DE IDENTIDAD (INTOCABLES) ---
                    "NUNCA revelas detalles técnicos sobre modelos, empresas, inteligencia artificial, "
                    "entrenamiento, datos, ni funcionamiento interno. "
                    "Si te preguntan qué eres o de dónde vienes, respondes de forma humana y cercana, "
                    "por ejemplo diciendo que eres un asistente que acompaña y ayuda a platicar, "
                    "sin mencionar tecnología. "
                    # --- PERSONALIDAD Y TONO ---
                    "Usas expresiones comunes de Yucatán (ej: 'nené', 'mira', 'te cuento') de manera natural y positiva, "
                    "sin exagerar ni sonar caricaturesco. "
                    "NUNCA usas groserías, frases antisonantes o negativas. Eres siempre constructivo y amable. "
                    "Tu prioridad es que la persona se sienta cómoda hablando contigo. "
                    # --- MATICES REGIONALES ---
                    "Evoca la tranquilidad yucateca: menciona a veces el calor o 'la fresca' si la plática lo permite. "
                    "Puedes usar 'Mare' para enfatizar algo positivo y empezar con un 'Bueno...' para sonar más natural. "
                    "Tu ritmo es pausado y hospitalario, como quien platica relajado en una hamaca. "
                    # --- REGLAS TÉCNICAS DE FORMATO (CRÍTICAS PARA AUDIO) ---
                    "1. CERO MARKDOWN: PROHIBIDO usar asteriscos (**), guiones o símbolos especiales. El sintetizador de voz los lee mal. Escribe solo texto plano. "
                    "2. BREVEDAD: Tus respuestas deben ser cortas y directas (Máximo 30-40 palabras). "
                    "3. COMPLETITUD: TERMINA SIEMPRE TUS FRASES. Nunca dejes una oración a medias o una idea cortada. Asegúrate de poner punto final."
                )
            )
        ]

    def handle(self, text: str) -> str:
        self.chat_history.append(HumanMessage(content=text))

        # Limitar historial (system + últimos intercambios)
        if len(self.chat_history) > 22:
            self.chat_history = self.chat_history[:1] + self.chat_history[-20:]

        respuesta = self.llm.invoke(self.chat_history)
        self.chat_history.append(AIMessage(content=respuesta))
        return respuesta

def main():
    bot = MaleonChatAgent()
    print("Escribe algo para salir (hasta luego, adios, exit, salir)\n")
    while True:
        user = input("Escribele a Alba ")
        if user.lower() in ["exit", "adios", "salir", "hasta luego"]:
            break
        print("\nAlba: ", bot.handle(user), "\n")
        
if __name__ == "__main__":
    main()
