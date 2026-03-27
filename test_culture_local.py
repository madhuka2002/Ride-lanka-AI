from services.gemini_service import get_place_culture

try:
    print("Testing get_place_culture...")
    data, source = get_place_culture("Sigiriya")
    print(f"Data: {data}")
    print(f"Source: {source}")
except Exception as e:
    import traceback
    traceback.print_exc()
