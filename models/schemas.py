from pydantic import BaseModel
from typing import List, Optional


class BehaviorEvent(BaseModel):
    place_name: str
    category: str  # culture, nature, beach, wildlife, food, adventure, hiking, dance
    action: str    # view, save, book, search


class RecommendationRequest(BaseModel):
    user_id: str
    interests: List[str]          # e.g. ["culture", "hiking", "dance"]
    behavior_queue: List[BehaviorEvent] = []   # up to 50 past events


class RecommendedPlace(BaseModel):
    name: str
    description: str
    category: str
    search_query: str            # used to look up on Google Maps
    place_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None
    maps_url: Optional[str] = None
    rating: Optional[float] = None


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendedPlace]
    source: str  # "gemini" or "fallback"
