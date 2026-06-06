"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


app = FastAPI(title="Nail Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "service": "nail-demo",
            "env": {
                "IMAGE_PROVIDER": settings.IMAGE_PROVIDER,
                "SCHEDULER_ENABLED": settings.SCHEDULER_ENABLED,
            },
        },
    }
