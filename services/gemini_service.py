import os
import json
import re
import time
import random
import math
import google.generativeai as genai  # type: ignore
from typing import List, Dict, Any
from services.fallback_data import FALLBACK_PLACES  # type: ignore

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 2.0 Flash — free tier (15 req/min, 1M tokens/day)
_model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={"temperature": 0.9}
)

def _score_place(place: Dict[str, Any], interests: List[str], behavior_queue: List[Dict[str, Any]]) -> float:
    score = 0.0
    cat = place.get("category", "")
    if interests and any(cat.lower() == i.lower() for i in interests):
        score += 3.0
    if behavior_queue:
        recent = behavior_queue[-10:]  # type: ignore
        for act in recent:
            if act.get("category", "").lower() == cat.lower():
                score += 1.0
    score += random.uniform(0.0, 0.5)
    return score

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
    route_preference: str = "shortest",
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

    algorithm_rules = ""
    if route_preference == "safest":
        algorithm_rules = "- Route Algorithm: Optimize for the 'safest path'. Prioritize major well-lit highways, popular tourist corridors, and populated safe areas. Avoid obscure backroads."
    elif route_preference == "max_places":
        algorithm_rules = "- Route Algorithm: Optimize for 'maximum places covering path'. Trace a main travel corridor and pack as many dense, high-quality attractions as possible within a strict 1km radius of the main driving path (i.e. cluster stops tightly along the core route to minimize detours)."
    else:
        algorithm_rules = "- Route Algorithm: Optimize for 'shortest path'. Order the stops strictly by geographic proximity to minimize total driving time and backtracking (solve the TSP efficiently)."

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
{algorithm_rules}
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
                print(f"[gemini_service] Rate limited — falling back instantly")
                break
            break

    scored_places = []  # type: ignore
    for p in FALLBACK_PLACES:
        s = _score_place(p, interests, behavior_queue)
        scored_places.append((s, p))
    scored_places.sort(key=lambda x: x[0], reverse=True)
    best_5 = [p for s, p in scored_places][:5]  # type: ignore
    return best_5, "fallback"


def get_trip_plan(
    trip_name: str,
    trip_date: str,
    stop_count: int,
    favorites: List[str],
    profile_interests: List[str],
    behavior_queue: List[Dict[str, Any]],
    route_preference: str = "shortest",
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
        route_preference=route_preference,
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
                        "lat": stop.get("lat"), # Include lat/lng if present
                        "lng": stop.get("lng"),
                    })



                return normalized, "gemini"
        except Exception as e:
            err_str = str(e)
            print(f"[gemini_service] Trip-plan Gemini error (attempt {attempt + 1}): {err_str[:200]}")  # type: ignore
            if "429" in err_str and attempt < 2:
                break
            break

    scored_places = []  # type: ignore
    for p in FALLBACK_PLACES:
        s = _score_place(p, profile_interests, behavior_queue)
        if favorites and any(p.get("name", "").lower() == f.lower() for f in favorites):
            s += 5.0
        scored_places.append((s, p.copy()))

    scored_places.sort(key=lambda x: x[0], reverse=True)
    best_stops = [p for s, p in scored_places][:stop_count]  # type: ignore
    
    if route_preference == "shortest":
        best_stops = __nearest_neighbor_sort(best_stops)
    else:
        for idx, s in enumerate(best_stops, start=1):
            s["stop_order"] = idx

    return best_stops, "fallback"


def __nearest_neighbor_sort(stops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not stops: return []
    valid_stops = [s for s in stops if s.get('lat') is not None and s.get('lng') is not None]
    if len(valid_stops) != len(stops):
        # Fallback to simple index sort if missing coordinates
        for idx, s in enumerate(stops, start=1):
            s["stop_order"] = idx
        return stops

    unvisited = valid_stops.copy()
    current = unvisited.pop(0)
    sorted_stops = [current]
    
    while unvisited:
        nearest = min(unvisited, key=lambda s: math.hypot(s['lat'] - current['lat'], s['lng'] - current['lng']))
        sorted_stops.append(nearest)
        unvisited.remove(nearest)
        current = nearest
        
    for idx, s in enumerate(sorted_stops, start=1):
        s["stop_order"] = idx
    return sorted_stops


def reorder_trip_plan(stops: List[Dict[str, Any]], route_preference: str) -> tuple[List[Dict[str, Any]], str]:
    if not stops:
        return [], "fallback"

    algorithm_rules = ""
    if route_preference == "safest":
        algorithm_rules = "Optimize for the 'safest path'. Prioritize major well-lit highways and popular corridors. Avoid obscure backroads."
    elif route_preference == "max_places":
        algorithm_rules = "Optimize for 'maximum places covering path'. Trace a main travel corridor and cluster stops tightly along the core route."
    else:
        algorithm_rules = "Optimize for 'shortest path'. Order the stops strictly by geographic proximity to minimize total driving time and backtracking."

    # Send stripped-down stops to save tokens
    simplified = [{"id": s.get("name"), "category": s.get("category")} for s in stops]

    prompt = f"""You are a geospatial algorithm optimizing a Sri Lanka trip.
I have a list of these exact places:
{json.dumps(simplified)}

Re-order these exact places based on this rule:
- {algorithm_rules}

Rules:
- DO NOT add or remove any places. You must return the exact same places provided in the input.
- Return ONLY a valid JSON array containing EXACTLY the original "id" strings. Do not invent new places.
Example output: ["Place C", "Place A", "Place B"]
"""
    for attempt in range(3):
        try:
            response = _model.generate_content(prompt)
            raw = response.text.strip()
            
            start_idx = raw.find('[')
            end_idx = raw.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                raw = raw[start_idx:end_idx]

            ordered_names = json.loads(raw)
            if isinstance(ordered_names, list) and len(ordered_names) == len(stops):
                new_stops = []
                stop_map = {s.get("name"): s for s in stops}
                for idx, name in enumerate(ordered_names, start=1):
                    original_stop = stop_map.get(name) or stops[idx - 1]
                    updated = original_stop.copy()
                    updated["stop_order"] = idx
                    new_stops.append(updated)
                return new_stops, "gemini"
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                break
            break

    # Fallback to local python geometric math if AI quota exhausted globally
    return __nearest_neighbor_sort(stops), "fallback"


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
        return {}, "error"

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
                break
            break

    return {}, "error"
