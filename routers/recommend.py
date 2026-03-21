import os
from fastapi import APIRouter, HTTPException, Header
from models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendedPlace,
    TripPlanRequest,
    TripPlanResponse,
    TripStop,
    CultureRequest,
    CultureResponse,
)
from services.gemini_service import get_recommendations, get_trip_plan, get_place_culture
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


@router.post("/trip-plan", response_model=TripPlanResponse)
async def trip_plan(
    payload: TripPlanRequest,
    x_backend_secret: str | None = Header(default=None),
):
    _verify_secret(x_backend_secret)

    if payload.stop_count < 1 or payload.stop_count > 20:
        raise HTTPException(status_code=400, detail="stop_count must be between 1 and 20")

    behavior_dicts = [e.model_dump() for e in payload.behavior_queue]

    raw_stops, source = get_trip_plan(
        trip_name=payload.trip_name,
        trip_date=payload.trip_date,
        stop_count=payload.stop_count,
        favorites=payload.favorites,
        profile_interests=payload.profile_interests,
        behavior_queue=behavior_dicts,
    )

    enriched = enrich_places(raw_stops)
    planned_stops = [TripStop(**s) for s in enriched]

    return TripPlanResponse(
        user_id=payload.user_id,
        trip_name=payload.trip_name,
        trip_date=payload.trip_date,
        stop_count=payload.stop_count,
        favorites=payload.favorites,
        source=source,
        stops=planned_stops,
    )


@router.post("/culture-info", response_model=CultureResponse)
async def culture_info(
    payload: CultureRequest,
    x_backend_secret: str | None = Header(default=None),
):
    _verify_secret(x_backend_secret)
    
    data, source = get_place_culture(payload.place_name)
    
    return CultureResponse(
        place_name=payload.place_name,
        dress_code=data.get("dress_code", ""),
        behavior_rules=data.get("behavior_rules", ""),
        best_season=data.get("best_season", ""),
        historical_context=data.get("historical_context", ""),
        source=source
    )
