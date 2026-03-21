import os
import httpx
from typing import List, Dict, Any, Optional

_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Google Places Text Search endpoint
_PLACES_TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
# Google Places Details endpoint
_PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
# Photo endpoint (returns redirect to actual image)
_PHOTO_BASE = "https://maps.googleapis.com/maps/api/place/photo"


def _get_photo_url(photo_reference: str, max_width: int = 800) -> str:
    return (
        f"{_PHOTO_BASE}?maxwidth={max_width}"
        f"&photoreference={photo_reference}"
        f"&key={_MAPS_API_KEY}"
    )


def enrich_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each place dict (which has a 'search_query'), call Google Places
    Text Search to get: place_id, lat, lng, photo_url, rating, maps_url.
    Works without an API key — fields will just remain None.
    """
    if not _MAPS_API_KEY:
        print("[places_service] No GOOGLE_MAPS_API_KEY — skipping enrichment")
        return places

    import time

    enriched = []
    with httpx.Client(timeout=10) as client:
        for place in places:
            try:
                time.sleep(0.15)  # Pause to avoid FREE TIER OVER_QUERY_LIMIT
                resp = client.get(
                    _PLACES_TEXT_SEARCH,
                    params={
                        "query": place.get("search_query", place["name"]),
                        "key": _MAPS_API_KEY,
                        "region": "lk",
                    },
                )
                data = resp.json()
                results = data.get("results", [])

                if results:
                    top = results[0]
                    place_id = top.get("place_id")
                    geometry = top.get("geometry", {}).get("location", {})
                    photos = top.get("photos", [])
                    photo_url = (
                        _get_photo_url(photos[0]["photo_reference"])
                        if photos
                        else None
                    )

                    place["place_id"] = place_id
                    place["lat"] = geometry.get("lat")
                    place["lng"] = geometry.get("lng")
                    place["photo_url"] = photo_url
                    place["rating"] = top.get("rating")
                    place["maps_url"] = (
                        f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                        if place_id
                        else None
                    )
            except Exception as e:
                print(f"[places_service] Error enriching '{place['name']}': {e}")

            enriched.append(place)

    return enriched
