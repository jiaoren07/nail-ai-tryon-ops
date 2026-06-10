"""C-end (consumer-side) routes.

CONVENTION (per implementation-plan §2.3):
All C-end routes — regardless of their URL second segment — live in this
single file. That includes (but is not limited to) future routes:
  /api/user/upload, /api/styles, /api/recommend, /api/tryon,
  /api/tryon/batch, /api/tryon/:id, /api/events/collect.

DO NOT create separate files like styles.py / recommend.py / tryon.py /
events.py. The filename `user.py` is shorthand for "C-end router",
not "only routes under /api/user/*".

auth note (per implementation-plan Step 4.1):
- The frontend generates `userId` (UUID v4) locally on first /upload visit
  and sends it as the HTTP header `X-User-Id` on every API request.
- The frontend stores `gender` in sessionStorage and sends it in the
  request body where relevant; the backend never persists session state.
- The backend will validate `X-User-Id` is a legal UUID string and reject
  otherwise; Step 4.1 implements that middleware.
"""
from fastapi import APIRouter

from app.responses import ok

router = APIRouter(prefix="/api")


@router.get("/ping")
def ping():
    """Liveness probe for the C-end router. Plan §2.3 verification target."""
    return ok(data={"router": "user"})
