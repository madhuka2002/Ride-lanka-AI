import os
from fastapi import APIRouter, HTTPException, Header
from models.schemas import RecommendationRequest, RecommendationResponse, RecommendedPlace
from services.gemini_service import get_recommendations
from services.places_service import enrich_places

router = APIRouter()

_BACKEND_SECRET = os.getenv("BACKEND_SECRET", "")


def _verify_secret(x_backend_secret: str | None):
    """Simple shared-secret auth between backend and AI service."""
    if _BACKEND_SECRET and x_backend_secret != _BACKEND_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend(
    payload: RecommendationRequest,
    x_backend_secret: str | None = Header(default=None),
):
    _verify_secret(x_backend_secret)

    # Convert Pydantic behavior events to plain dicts for service functions
    behavior_dicts = [e.model_dump() for e in payload.behavior_queue]

    # 1. Ask Gemini for top-5 place recommendations
    raw_places, source = get_recommendations(payload.interests, behavior_dicts)

    # 2. Enrich with Google Maps data (coordinates, photo, maps URL)
    enriched = enrich_places(raw_places)

    # 3. Build response
    recommended = [RecommendedPlace(**p) for p in enriched]

    return RecommendationResponse(
        user_id=payload.user_id,
        recommendations=recommended,
        source=source,
    )
