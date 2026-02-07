import speech_recognition as sr
import json
from typing import Literal

class modulo_transcriptor:

    def __init__(self, method: Literal["whisper", "google", "sphinx"] = "google"):
        self.recognizer = sr.Recognizer()
        self.method = method
        
        try:
            self.microfono = sr.Microphone()
        except Exception as e:
            print(f"Advertencia: Micrófono no disponible: {e}")
            self.microfono = None

        self.recognizer.pause_threshold = 1.0
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

    def listar_microfonos(self) -> list:
        try:
            return sr.Microphone.list_microphone_names()
        except:
            return []

    def transcribir_desde_micrófono(self, lenguaje: str = "es-ES"):
        if self.microfono is None:
            return {"success": False, "error": "Micrófono no disponible. PyAudio no instalado correctamente."}
        
        try:
            with self.microfono as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                grabacion = self.recognizer.listen(source)
                text = self._recognize_audio(grabacion, lenguaje)

                return {
                    "success": True,
                    "text": text,
                    "method": self.method
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _recognize_audio(self, grabacion_data, language: str) -> str:
        if self.method == "google":
            return self.recognizer.recognize_google(grabacion_data, language=language)
        elif self.method == "whisper":
            return self.recognizer.recognize_whisper(grabacion_data, language=language[:2], model="small")
        elif self.method == "sphinx":
            return self.recognizer.recognize_sphinx(grabacion_data, language=language)
