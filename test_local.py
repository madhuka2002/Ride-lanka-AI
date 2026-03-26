from services.gemini_service import get_recommendations

try:
    best_5, source = get_recommendations(["nature", "beach"], [])
    for p in best_5:
        print(p["name"], p["category"])
    print("Source:", source)
except Exception as e:
    import traceback
    traceback.print_exc()
