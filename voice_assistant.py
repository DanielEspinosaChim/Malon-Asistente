import time
from audio_transcriptor import modulo_transcriptor
from Agente import MaleonChatAgent
import pyttsx3

if __name__ == "__main__":
    transcriptor = modulo_transcriptor(method="google")
    bot = MaleonChatAgent()
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  
    engine.setProperty("volume", 1.0)

    print("\n🟢 Maleon listo. Habla por el micrófono.\n")

    while True:
        try:
            print("🎙️ Escuchando voz (habla ahora)...", end=" ", flush=True)
            r = transcriptor.transcribir_desde_micrófono("es-ES")

            if not r["success"]:
                print(f"\n❌ {r.get('error', 'Error')}")
                continue

            texto = r["text"].strip()
            print(f"\n🧑: {texto}")

            if texto.lower() in ["salir", "exit", "adios", "bye"]:
                print("\n👋 Cerrando Maleon\n")
                break

            respuesta = bot.handle(texto)
            respuesta_hablada = (
                respuesta
                .replace(",", ", … ")
                .replace(".", ". … ")
            )

            print(f"🤖 Maleon: {respuesta}\n")

            # Maleon habla
            engine.say(respuesta_hablada)
            engine.runAndWait()

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n\n👋 Cerrando Malon\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            continue
