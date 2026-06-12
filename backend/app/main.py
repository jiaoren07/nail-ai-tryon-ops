"""FastAPI application entrypoint."""
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


# Plan §4.1: every /api/... request (except /api/health) must carry a
# legal UUID v4 in the X-User-Id header. CORS preflight (OPTIONS) is
# exempt — browsers do not attach custom headers to preflight.
@app.middleware("http")
async def require_user_id(request: Request, call_next):
    path = request.url.path
    if (
        path.startswith("/api/")
        and path != "/api/health"
        and request.method != "OPTIONS"
    ):
        raw = request.headers.get("X-User-Id")
        try:
            uuid.UUID(raw)
        except (ValueError, TypeError, AttributeError):
            return JSONResponse(
                status_code=400,
                content={"code": 400, "msg": "invalid_user_id", "data": None},
            )
    return await call_next(request)

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
