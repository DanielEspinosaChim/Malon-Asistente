from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()

# Texto con modismos yucatecos
texto = "¡Qué onda, mare! Ya quedó la voz. No te fijes que diga es-US, vas a ver que sueno bien yucateco con estos ajustes."
synthesis_input = texttospeech.SynthesisInput(text=texto)

# Usamos la voz que SÍ tienes disponible y es de alta calidad (Neural2)
voice = texttospeech.VoiceSelectionParams(
    language_code="es-US", 
    name="es-US-Neural2-B"
)

# EL TRUCO PARA EL ACENTO:
# pitch: -4.0 (Hace la voz más grave y "golpeada")
# speaking_rate: 0.85 (Hace que hable pausado, estilo yucateco)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    pitch=-4.0, 
    speaking_rate=0.85
)

print("Generando audio yucateco con voz Neural2...")
response = client.synthesize_speech(
    input=synthesis_input, 
    voice=voice, 
    audio_config=audio_config
)

with open("prueba_maleon.mp3", "wb") as out:
    out.write(response.audio_content)
    print("---------------------------------------------------------")
    print("¡LISTO! Escucha el archivo 'prueba_maleon.mp3'.")
    print("---------------------------------------------------------")