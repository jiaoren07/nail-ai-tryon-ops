"""Unified response envelope: {code, msg, data} for both success and error."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("nail_demo")


def ok(data: Any = None, msg: str = "ok") -> dict:
    """Build a success envelope. Routes return `ok(data=...)` instead of dict literals."""
    return {"code": 0, "msg": msg, "data": data}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException -> {code: status_code, msg: detail, data: null} with matching HTTP status."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": str(exc.detail), "data": None},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Generic exception catch-all: log at ERROR + return code=500 envelope."""
    logger.exception(
        "unhandled exception in %s %s: %r", request.method, request.url.path, exc
    )
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "internal_error", "data": None},
    )
