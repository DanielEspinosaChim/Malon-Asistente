import uuid
import os
from google.cloud import texttospeech
from app.config import PROJECT_ID

class TTSService:

    def __init__(self):
        self.client = texttospeech.TextToSpeechClient(
            client_options={"quota_project_id": PROJECT_ID}
        )

    def synthesize(self, text: str):
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="es-US",
            name="es-US-Neural2-B"
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=-4.0,
            speaking_rate=0.85
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        filename = f"{uuid.uuid4()}.mp3"
        os.makedirs("temp_audio", exist_ok=True)
        filepath = os.path.join("temp_audio", filename)

        with open(filepath, "wb") as out:
            out.write(response.audio_content)

        return f"/temp_audio/{filename}"
