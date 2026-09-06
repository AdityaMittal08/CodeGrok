import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers import ingest, search, explain
app = FastAPI()

app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(explain.router)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CODEGROK_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Codegrok-Key"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "codegrok-api"}