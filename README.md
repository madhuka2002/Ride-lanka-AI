# Ride Lanka AI Service

FastAPI microservice that powers AI-driven travel recommendations using **Gemini 1.5 Flash** and **Google Maps Places API**.

## How it works

1. Receives a user's **interests** (e.g. `["culture", "hiking"]`) and their **behavior queue** (up to 50 past interactions)
2. Builds a structured prompt and calls **Gemini 1.5 Flash** (free tier)
3. Gets back 5 recommended Sri Lanka destinations
4. Enriches each place via **Google Maps Places API** (coordinates, photo, rating, maps link)
5. Returns the enriched list to the backend

## Setup

```bash
cd Ride-lanka-AI
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # fill in your API keys
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Environment variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Get free at https://aistudio.google.com/app/apikey |
| `GOOGLE_MAPS_API_KEY` | Google Cloud Console — enable Places API |
| `BACKEND_SECRET` | Shared secret with `Ride-lanka-backend` |

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/ai/recommend` | Get top-5 recommendations |

### POST `/api/ai/recommend`

**Request body:**
```json
{
  "user_id": "uid_abc123",
  "interests": ["culture", "hiking", "wildlife"],
  "behavior_queue": [
    { "place_name": "Sigiriya", "category": "culture", "action": "view" }
  ]
}
```

**Response:**
```json
{
  "user_id": "uid_abc123",
  "source": "gemini",
  "recommendations": [
    {
      "name": "Sigiriya Rock Fortress",
      "description": "Ancient fortress with panoramic views",
      "category": "culture",
      "search_query": "Sigiriya Rock Fortress Sri Lanka",
      "place_id": "ChIJ...",
      "lat": 7.9572,
      "lng": 80.7603,
      "photo_url": "https://maps.googleapis.com/...",
      "maps_url": "https://www.google.com/maps/place/?q=place_id:ChIJ...",
      "rating": 4.7
    }
  ]
}
```

## Cost (free tier)

- **Gemini 1.5 Flash**: 15 RPM, 1M tokens/day — **free**
- **Google Maps Places**: $200/month credit ≈ 4,000 text searches — **effectively free** for early-stage
