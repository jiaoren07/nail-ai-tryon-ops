"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Nail Demo API", version="0.1.0", lifespan=lifespan)

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
