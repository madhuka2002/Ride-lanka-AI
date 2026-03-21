import os
import sys

# Change to correct dir if needed
from dotenv import load_dotenv
load_dotenv()

from services.gemini_service import get_trip_plan, get_recommendations

print("Testing Gemini...")
try:
    stops, source = get_trip_plan(
        trip_name="Test",
        trip_date="2026-03-25",
        stop_count=5,
        favorites=["hiking", "dance", "culture"],
        profile_interests=["nature"],
        behavior_queue=[]
    )
    print(f"TRIP Source: {source}")
    print(stops)
except Exception as e:
    import traceback
    traceback.print_exc()

import sys
sys.stdout.flush()
