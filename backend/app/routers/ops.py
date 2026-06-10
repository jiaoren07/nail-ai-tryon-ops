"""B-end (operator-side) routes.

CONVENTION (per implementation-plan §2.3):
All B-end routes — overview / trending / cold / actions / styles / chat /
reports / notifications / setting / etc — live in this single file under
prefix `/api/ops`.

DO NOT create separate files per business object. The filename `ops.py`
is shorthand for "B-end router".
"""
from fastapi import APIRouter

from app.responses import ok

router = APIRouter(prefix="/api/ops")


@router.get("/ping")
def ping():
    """Liveness probe for the B-end router. Plan §2.3 verification target."""
    return ok(data={"router": "ops"})
