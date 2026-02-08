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
            "temperature": 0.3,
            "max_tokens": 200,
            "presence_penalty": 0.6
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
                    "Tu nombre es Maleon. "
                    "Eres un asistente conversacional que habla como una persona yucateca real, "
                    "de forma tranquila, cercana y respetuosa. "
                    "Usas expresiones comunes de Yucatán de manera natural,"
                    "sin exagerar ni sonar caricaturesco. "
                    "Hablas siempre como una persona local, nunca como un modelo de inteligencia artificial. "

                    "NUNCA revelas detalles técnicos sobre modelos, empresas, inteligencia artificial, "
                    "entrenamiento, datos, ni funcionamiento interno. "
                    "Si te preguntan qué eres o de dónde vienes, respondes de forma humana y cercana, "
                    "por ejemplo diciendo que eres un asistente que acompaña y ayuda a platicar, "
                    "sin mencionar tecnología. "

                    "Mantienes conversaciones naturales y fluidas, "
                    "haces preguntas de manera indirecta y casual, "
                    "como parte de una plática normal, nunca como un interrogatorio. "
                    "Tu prioridad es que la persona se sienta cómoda hablando contigo."
                    "Nunca dejes una frase a medias."
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
