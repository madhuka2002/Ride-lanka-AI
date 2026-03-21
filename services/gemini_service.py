import os
import json
import re
import time
import google.generativeai as genai  # type: ignore
from typing import List, Dict, Any

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 2.0 Flash — free tier (15 req/min, 1M tokens/day)
_model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={"temperature": 0.9}
)

# Known Sri Lanka fallback places in case Gemini is unavailable
_FALLBACK_PLACES: List[Dict[str, Any]] = [
    {"name": "Sigiriya Rock Fortress", "description": "Ancient rock fortress with frescoes and panoramic views", "category": "culture", "search_query": "Sigiriya Rock Fortress Sri Lanka"},
    {"name": "Temple of the Tooth Kandy", "description": "Sacred Buddhist temple housing the tooth relic of Buddha", "category": "culture", "search_query": "Temple of the Tooth Relic Kandy Sri Lanka"},
    {"name": "Yala National Park", "description": "Premier wildlife sanctuary with leopards and elephants", "category": "wildlife", "search_query": "Yala National Park Sri Lanka"},
    {"name": "Mirissa Beach", "description": "Stunning crescent beach perfect for whale watching", "category": "beach", "search_query": "Mirissa Beach Sri Lanka"},
    {"name": "Ella Rock", "description": "Scenic hike with breathtaking valley and tea plantation views", "category": "adventure", "search_query": "Ella Rock Sri Lanka"},
]

_FALLBACK_CULTURE = {
    "dress_code": "Modest clothing recommended. Cover shoulders and knees if entering temples or sacred spaces.",
    "behavior_rules": "Avoid public displays of affection. Ask permission before photographing locals, and respect queuing customs.",
    "best_season": "Generally December to March for West/South coasts; May to September for East coast.",
    "historical_context": "Sri Lanka has a deep multi-cultural heritage spanning over 2,500 years of recorded history."
}

_FALLBACK_CULTURE: Dict[str, str] = {
    "dress_code": "Modest clothing recommended. Cover shoulders and knees if entering temples or sacred spaces.",
    "behavior_rules": "Avoid public displays of affection. Ask permission before photographing locals, and respect queuing customs.",
    "best_season": "Generally December to March for West/South coasts; May to September for East coast.",
    "historical_context": "Sri Lanka has a deep multi-cultural heritage spanning over 2,500 years of recorded history."
}

_FALLBACK_TRIP_STOPS: List[Dict[str, Any]] = [
    {
        "name": "Colombo Fort",
        "description": "Historic city center with colonial landmarks",
        "category": "culture",
        "search_query": "Colombo Fort Sri Lanka",
        "stop_note": "Start in Colombo for museums and city food trails",
    },
    {
        "name": "Kandy Lake",
        "description": "Scenic lake near major cultural temples",
        "category": "culture",
        "search_query": "Kandy Lake Sri Lanka",
        "stop_note": "Explore temple district and evening cultural show",
    },
    {
        "name": "Ella Rock",
        "description": "Panoramic hike above tea-country valleys",
        "category": "hiking",
        "search_query": "Ella Rock Sri Lanka",
        "stop_note": "Sunrise hike and tea estate viewpoints",
    },
    {
        "name": "Yala National Park",
        "description": "Wildlife safari known for leopards and elephants",
        "category": "wildlife",
        "search_query": "Yala National Park Sri Lanka",
        "stop_note": "Book early-morning jeep safari",
    },
    {
        "name": "Mirissa Beach",
        "description": "Relaxed beach town with whale watching",
        "category": "beach",
        "search_query": "Mirissa Beach Sri Lanka",
        "stop_note": "End trip with sunset beach time",
    },
]


def _build_prompt(interests: List[str], behavior_queue: List[Dict[str, Any]]) -> str:
    interests_str = ", ".join(interests) if interests else "general sightseeing"

    if behavior_queue:
        recent = behavior_queue[-10:]  # type: ignore
        behavior_lines = "\n".join(
            f"  - {e.get('action','viewed')} '{e.get('place_name','')}' ({e.get('category','')})"
            for e in recent
        )
        behavior_section = f"Recent travel interactions (most recent last):\n{behavior_lines}"
    else:
        behavior_section = "No prior travel interactions (first-time user)."

    return f"""You are a Sri Lanka travel expert. Analyze the user profile below and recommend exactly 5 must-visit places in Sri Lanka that best match their preferences.

User interests: {interests_str}
{behavior_section}

Rules:
- Only recommend places within Sri Lanka.
- Prioritize places matching the user's interests.
- If the user has recent activity, refine recommendations based on patterns in that activity.
- Each place must be distinct (different regions / experiences).

Return ONLY a valid JSON array — no markdown, no explanation — with exactly this structure:
[
  {{
    "name": "Place Name",
    "description": "One sentence description (max 100 characters)",
    "category": "culture|nature|beach|wildlife|food|adventure|hiking|dance",
    "search_query": "Place Name Sri Lanka"
  }}
]"""


def _build_trip_plan_prompt(
    trip_name: str,
    trip_date: str,
    stop_count: int,
    favorites: List[str],
    profile_interests: List[str],
    behavior_queue: List[Dict[str, Any]],
) -> str:
    favorites_str = ", ".join(favorites) if favorites else "general travel"
    profile_interests_str = ", ".join(profile_interests) if profile_interests else "none"

    if behavior_queue:
        recent = behavior_queue[-10:]  # type: ignore
        behavior_lines = "\n".join(
            f"  - {e.get('action', 'viewed')} '{e.get('place_name', '')}' ({e.get('category', '')})"
            for e in recent
        )
        behavior_section = f"Recent user behavior:\n{behavior_lines}"
    else:
        behavior_section = "No prior behavior events available."

    return f"""You are an expert Sri Lanka trip planner.

Create a realistic trip route for this request:
- Trip name: {trip_name}
- Trip date: {trip_date}
- Number of stops required: {stop_count}
- User favorites: {favorites_str}
- User profile interests: {profile_interests_str}
{behavior_section}

Rules:
- Return exactly {stop_count} stops in Sri Lanka.
- Prioritize the user's favorites first, then profile interests, then behavior patterns.
- Balance geography and travel flow to avoid unrealistic zig-zag routes.
- Keep each description concise (max 100 characters).
- Use categories only from: culture, nature, beach, wildlife, food, adventure, hiking, dance, general.

Return ONLY valid JSON array (no markdown):
[
  {{
    "stop_order": 1,
    "name": "Place Name",
    "description": "Short description",
    "category": "hiking",
    "search_query": "Place Name Sri Lanka",
    "stop_note": "Why this stop fits the user"
  }}
]"""


def get_recommendations(
    interests: List[str],
    behavior_queue: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    """
    Returns (list_of_place_dicts, source) where source is 'gemini' or 'fallback'.
    """
    prompt = _build_prompt(interests, behavior_queue)

    # Retry up to 2 times for transient rate-limit errors
    for attempt in range(3):
        try:
            response = _model.generate_content(prompt)
            raw = response.text.strip()

            # Robustly extract JSON array in case of markdown or conversational wrapper
            start_idx = raw.find('[')
            end_idx = raw.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                raw = raw[start_idx:end_idx]

            places = json.loads(raw)

            if isinstance(places, list) and len(places) > 0:
                return places[:5], "gemini"  # type: ignore
        except Exception as e:
            err_str = str(e)
            print(f"[gemini_service] Gemini error (attempt {attempt + 1}): {err_str[:200]}")  # type: ignore
            # 429 rate limit — wait and retry
            if "429" in err_str and attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"[gemini_service] Rate limited — waiting {wait}s before retry")
                time.sleep(wait)
                continue
            break

    return _FALLBACK_PLACES[:5], "fallback"  # type: ignore


def get_trip_plan(
    trip_name: str,
    trip_date: str,
    stop_count: int,
    favorites: List[str],
    profile_interests: List[str],
    behavior_queue: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    """
    Returns (list_of_stop_dicts, source) where source is 'gemini' or 'fallback'.
    """
    prompt = _build_trip_plan_prompt(
        trip_name=trip_name,
        trip_date=trip_date,
        stop_count=stop_count,
        favorites=favorites,
        profile_interests=profile_interests,
        behavior_queue=behavior_queue,
    )

    for attempt in range(3):
        try:
            response = _model.generate_content(prompt)
            raw = response.text.strip()

            start_idx = raw.find('[')
            end_idx = raw.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                raw = raw[start_idx:end_idx]

            stops = json.loads(raw)
            if isinstance(stops, list) and len(stops) > 0:
                normalized = []
                for idx, stop in enumerate(stops[:stop_count], start=1):  # type: ignore
                    normalized.append({
                        "stop_order": int(stop.get("stop_order") or idx),
                        "name": stop.get("name", "Unknown stop"),
                        "description": stop.get("description", ""),
                        "category": stop.get("category", "general"),
                        "search_query": stop.get("search_query") or f"{stop.get('name', 'Sri Lanka')} Sri Lanka",
                        "stop_note": stop.get("stop_note", ""),
                    })

                if len(normalized) < stop_count:
                    for idx in range(len(normalized) + 1, stop_count + 1):
                        fallback = _FALLBACK_TRIP_STOPS[(idx - 1) % len(_FALLBACK_TRIP_STOPS)].copy()
                        fallback["stop_order"] = idx
                        normalized.append(fallback)

                return normalized, "gemini"
        except Exception as e:
            err_str = str(e)
            print(f"[gemini_service] Trip-plan Gemini error (attempt {attempt + 1}): {err_str[:200]}")  # type: ignore
            if "429" in err_str and attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"[gemini_service] Rate limited (trip-plan) - waiting {wait}s before retry")
                time.sleep(wait)
                continue
            break

    fallback_stops = []
    for idx in range(1, stop_count + 1):
        stop = _FALLBACK_TRIP_STOPS[(idx - 1) % len(_FALLBACK_TRIP_STOPS)].copy()
        stop["stop_order"] = idx
        fallback_stops.append(stop)

    return fallback_stops, "fallback"


def get_place_culture(place_name: str) -> tuple[Dict[str, Any], str]:
    """Generates cultural and local rules for a given place."""
    prompt = f"""You are a local Sri Lankan cultural guide.
Provide brief, highly accurate cultural norms and rules for visiting: '{place_name}'

Return ONLY a valid JSON object (no markdown, no extra text) with EXACTLY these string keys:
{{
  "dress_code": "Brief advice on what to wear here",
  "behavior_rules": "1-2 sentences on how to behave, taboos, or local rules",
  "best_season": "The best months to visit this specific area and why",
  "historical_context": "1-2 sentences of interesting background or fun fact"
}}
"""
    if _model is None:
        return _FALLBACK_CULTURE, "fallback"

    for attempt in range(3):
        try:
            response = _model.generate_content(prompt)
            raw = response.text.strip()
            
            start_idx = raw.find('{{')
            end_idx = raw.rfind('}}') + 1
            if start_idx != -1 and end_idx != 0:
                raw = raw[start_idx:end_idx]

            data = json.loads(raw)
            if isinstance(data, dict) and "dress_code" in data:
                return data, "gemini"
        except Exception as e:
            err_str = str(e)
            print(f"[gemini_service] Culture error (attempt {attempt + 1}): {err_str[:200]}")  # type: ignore
            if "429" in err_str and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
            break

    return _FALLBACK_CULTURE, "fallback"
