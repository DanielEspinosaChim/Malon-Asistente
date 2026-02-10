import os
import json
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=PROJECT_ID, location="us-central1")

class MaleonChatAgent:
    def __init__(self, storage_file="memoria_maleon.json"):
    
        self.model = GenerativeModel("gemini-2.5-flash")
        self.storage_file = storage_file
        
      
        self.system_instruction = (
            "Tu nombre es Maleon. "
            "Hablas como una persona yucateca real, de forma tranquila, cercana y respetuosa. "
            "Usas expresiones comunes de Yucatán de manera natural, sin exagerar. "
            "Hablas como un local, NUNCA menciones que eres una IA, ni reveles detalles técnicos. "
            "Si te preguntan qué eres, di que eres un asistente que acompaña y ayuda a platicar. "
            "Mantienes pláticas fluidas y casuales, nunca interrogatorios."
        )
     
        self.history = self._load_memory()
        
      
        self.chat = self.model.start_chat(history=self.history)

    def _load_memory(self):
        """Carga la plática del JSON y la convierte al formato de Vertex AI."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                 
                    return [Content(role=m['role'], parts=[Part.from_text(m['content'])]) for m in data]
            except Exception as e:
                print(f"Aviso: No se pudo cargar la memoria previa ({e}). Empezando de cero.")
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
        """Maneja el mensaje del usuario y guarda la respuesta."""

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