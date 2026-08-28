"""FastAPI application entrypoint."""
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
from app.services.report import generate_and_dispatch_report

BACKEND_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = BACKEND_ROOT / "static"

_log = logging.getLogger("nail_demo.main")

# Step 9.2: in-process scheduler (design-docu §7.7.2). Module-level so the
# debug/introspection code can reach it; started only when
# SCHEDULER_ENABLED and always shut down on app exit.
# timezone is EXPLICIT on every trigger — a UTC host would otherwise fire
# "09:00" eight hours late (plan §9.2 hard requirement).
scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

_MISFIRE_GRACE_SECONDS = 3600


async def _run_daily_report() -> None:
    await generate_and_dispatch_report("daily", "scheduled")


async def _run_weekly_report() -> None:
    await generate_and_dispatch_report("weekly", "scheduled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if settings.SCHEDULER_ENABLED:
        scheduler.add_job(
            _run_daily_report,
            CronTrigger(hour=9, minute=0, timezone="Asia/Shanghai"),
            id="daily_report",
            misfire_grace_time=_MISFIRE_GRACE_SECONDS,
        )
        scheduler.add_job(
            _run_weekly_report,
            CronTrigger(day_of_week="mon", hour=9, minute=0, timezone="Asia/Shanghai"),
            id="weekly_report",
            misfire_grace_time=_MISFIRE_GRACE_SECONDS,
        )
        scheduler.start()
        _log.info(
            "Scheduler started (Asia/Shanghai): %s",
            [f"{j.id} next={j.next_run_time}" for j in scheduler.get_jobs()],
        )
    else:
        _log.info("Scheduler disabled via SCHEDULER_ENABLED=false")
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


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
