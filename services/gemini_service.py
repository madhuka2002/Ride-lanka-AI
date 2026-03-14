import os
import json
import re
import time
import google.generativeai as genai
from typing import List, Dict, Any

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 2.0 Flash — free tier (15 req/min, 1M tokens/day)
_model = genai.GenerativeModel("gemini-2.0-flash")

# Known Sri Lanka fallback places in case Gemini is unavailable
_FALLBACK_PLACES = [
    {"name": "Sigiriya Rock Fortress", "description": "Ancient rock fortress with frescoes and panoramic views", "category": "culture", "search_query": "Sigiriya Rock Fortress Sri Lanka"},
    {"name": "Temple of the Tooth Kandy", "description": "Sacred Buddhist temple housing the tooth relic of Buddha", "category": "culture", "search_query": "Temple of the Tooth Relic Kandy Sri Lanka"},
    {"name": "Yala National Park", "description": "Premier wildlife sanctuary with leopards and elephants", "category": "wildlife", "search_query": "Yala National Park Sri Lanka"},
    {"name": "Mirissa Beach", "description": "Stunning crescent beach perfect for whale watching", "category": "beach", "search_query": "Mirissa Beach Sri Lanka"},
    {"name": "Ella Rock", "description": "Scenic hike with breathtaking valley and tea plantation views", "category": "adventure", "search_query": "Ella Rock Sri Lanka"},
]


def _build_prompt(interests: List[str], behavior_queue: List[Dict[str, Any]]) -> str:
    interests_str = ", ".join(interests) if interests else "general sightseeing"

    if behavior_queue:
        recent = behavior_queue[-10:]  # last 10 events for brevity
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

            # Strip markdown code fences if present
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            places = json.loads(raw)

            if isinstance(places, list) and len(places) > 0:
                return places[:5], "gemini"
        except Exception as e:
            err_str = str(e)
            print(f"[gemini_service] Gemini error (attempt {attempt + 1}): {err_str[:200]}")
            # 429 rate limit — wait and retry
            if "429" in err_str and attempt < 2:
                wait = 15 * (attempt + 1)
                print(f"[gemini_service] Rate limited — waiting {wait}s before retry")
                time.sleep(wait)
                continue
            break

    return _FALLBACK_PLACES[:5], "fallback"
