"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db import init_db
from app.responses import (
    http_exception_handler,
    ok,
    unhandled_exception_handler,
)
from app.routers import ops as ops_router
from app.routers import user as user_router

BACKEND_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = BACKEND_ROOT / "static"


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

# Register on Starlette's HTTPException (parent of fastapi.HTTPException) so
# StaticFiles 404 + unmatched-route 404 also get the envelope, not the default
# {"detail": "..."} shape.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(user_router.router)
app.include_router(ops_router.router)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/health")
def health() -> dict:
    return ok(data={
        "service": "nail-demo",
        "env": {
            "IMAGE_PROVIDER": settings.IMAGE_PROVIDER,
            "SCHEDULER_ENABLED": settings.SCHEDULER_ENABLED,
        },
    })
