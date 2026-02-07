from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from Agente import MaleonChatAgent

app = FastAPI()
bot = MaleonChatAgent()

# Montamos las carpetas para que sean accesibles desde el navegador
app.mount("/avatar", StaticFiles(directory="avatar"), name="avatar")
app.mount("/static", StaticFiles(directory="static"), name="static")

class Msg(BaseModel):
    text: str

@app.get("/")
async def index():
    return FileResponse("static/index.html")

@app.post("/chat")
async def chat(msg: Msg):
    # Llama a tu método handle en Agente.py
    respuesta = bot.handle(msg.text)
    return {"reply": respuesta}