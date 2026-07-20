"""AI capability status.

One place for clients and operators to see which advice/vision backends are
active and whether photo features would actually work right now — so the
mobile app can gate its photo UI on reality instead of finding out via a
stub answer, and a fresh deploy can be smoke-checked with one GET.

Unauthenticated on purpose (like `/`): it exposes backend/model names only,
never hosts or secrets.
"""
from fastapi import APIRouter

from app.services import advisor
from app.services.vision import vision_status

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def ai_status():
    return {
        "advisor_backend": advisor.BACKEND,
        "advisor_symptoms_backend": advisor.SYMPTOMS_BACKEND,
        "vision": await vision_status(),
    }
