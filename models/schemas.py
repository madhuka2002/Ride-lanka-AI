from pydantic import BaseModel, Field
from typing import List, Optional


class BehaviorEvent(BaseModel):
    place_name: str
    category: str  # culture, nature, beach, wildlife, food, adventure, hiking, dance
    action: str    # view, save, book, search


class RecommendationRequest(BaseModel):
    user_id: str
    interests: List[str]          # e.g. ["culture", "hiking", "dance"]
    behavior_queue: List[BehaviorEvent] = Field(default_factory=list)   # up to 50 past events


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


class TripPlanRequest(BaseModel):
    user_id: str
    trip_name: str
    trip_date: str
    stop_count: int
    favorites: List[str] = Field(default_factory=list)
    profile_interests: List[str] = Field(default_factory=list)
    behavior_queue: List[BehaviorEvent] = Field(default_factory=list)


class TripStop(BaseModel):
    stop_order: int
    name: str
    description: str
    category: str
    search_query: str
    stop_note: Optional[str] = None
    place_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None
    maps_url: Optional[str] = None
    rating: Optional[float] = None


class TripPlanResponse(BaseModel):
    user_id: str
    trip_name: str
    trip_date: str
    stop_count: int
    favorites: List[str]
    source: str
    stops: List[TripStop]


class CultureRequest(BaseModel):
    place_name: str


class CultureResponse(BaseModel):
    place_name: str
    dress_code: str
    behavior_rules: str
    best_season: str
    historical_context: str
    source: str

class PlaceSearchRequest(BaseModel):
    query: str
