from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers.chat import router as chat_router
from app.config import PROJECT_ID, CACHE_FILE, BLACKLIST

app = FastAPI()

app.mount("/avatar", StaticFiles(directory="avatar"), name="avatar")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp_audio", StaticFiles(directory="temp_audio"), name="temp_audio")

app.include_router(chat_router)

@app.get("/")
async def index():
    return FileResponse("static/index.html")
