import json
import random

# Core lists of pure Sri Lankan places & features
CITIES = [
    {"city": "Colombo", "region": "West", "base_lat": 6.927, "base_lng": 79.861},
    {"city": "Kandy", "region": "Central", "base_lat": 7.290, "base_lng": 80.633},
    {"city": "Galle", "region": "South", "base_lat": 6.032, "base_lng": 80.217},
    {"city": "Ella", "region": "Uva", "base_lat": 6.866, "base_lng": 81.046},
    {"city": "Nuwara Eliya", "region": "Central", "base_lat": 6.949, "base_lng": 80.783},
    {"city": "Sigiriya", "region": "North Central", "base_lat": 7.957, "base_lng": 80.760},
    {"city": "Mirissa", "region": "South", "base_lat": 5.948, "base_lng": 80.467},
    {"city": "Yala", "region": "South", "base_lat": 6.368, "base_lng": 81.517},
    {"city": "Jaffna", "region": "North", "base_lat": 9.661, "base_lng": 80.025},
    {"city": "Trincomalee", "region": "East", "base_lat": 8.587, "base_lng": 81.215},
    {"city": "Anuradhapura", "region": "North Central", "base_lat": 8.311, "base_lng": 80.403},
    {"city": "Arugam Bay", "region": "East", "base_lat": 6.843, "base_lng": 81.826},
    {"city": "Polonnaruwa", "region": "North Central", "base_lat": 7.940, "base_lng": 81.018},
    {"city": "Negombo", "region": "West", "base_lat": 7.200, "base_lng": 79.833},
    {"city": "Bentota", "region": "South", "base_lat": 6.428, "base_lng": 79.999}
]

CATEGORIES = [
    ("culture", ["Temple", "Ancient Ruins", "Fort", "Museum", "Historical Site", "Palace Rerains"]),
    ("nature", ["Botanical Garden", "Waterfall", "Lake", "Mountain Viewpoint", "Tea Estate", "Forest Reserve"]),
    ("beach", ["Sandy Beach", "Surfing Spot", "Coral Reef", "Secluded Cove", "Turtle Hatchery", "Sunset Point"]),
    ("wildlife", ["National Park", "Elephant Orphanage", "Bird Sanctuary", "Safari Zone", "Leopard Viewpoint", "Whale Watching Hub"]),
    ("food", ["Spice Market", "Seafood Street", "Street Food Market", "Traditional Cafe", "Tea Factory", "Local Farm"]),
    ("adventure", ["Zip Line", "White Water Rafting", "Rock Climbing", "Cave Exploration", "Kite Surfing Start", "Jungle Trek"]),
    ("hiking", ["Mountain Peak", "Nature Trail", "Valley Hike", "Ridge Walk", "Forest Path", "Clifftop Trail"]),
    ("dance", ["Traditional Mask Dance Hall", "Cultural Show Arena", "Kandyan Dance Theatre", "Fire Dance Pavilion", "Folk Arts Center"]),
    ("general", ["City Square", "Local Bazaar", "Shopping District", "Guesthouse Street", "Train Station View", "Town Center"])
]

places = []
place_names = set()

# Seed specific famous places
FAMOUS = [
    ("Sigiriya Rock Fortress", "culture", "Ancient rock fortress with frescoes and panoramic views.", "Sigiriya", 7.957, 80.760),
    ("Temple of the Tooth", "culture", "Sacred Buddhist temple housing the tooth relic of Buddha.", "Kandy", 7.293, 80.641),
    ("Yala National Park", "wildlife", "Premier wildlife sanctuary with leopards and elephants.", "Yala", 6.368, 81.517),
    ("Mirissa Beach", "beach", "Stunning crescent beach perfect for whale watching.", "Mirissa", 5.948, 80.467),
    ("Ella Rock", "hiking", "Scenic hike with breathtaking valley and tea plantation views.", "Ella", 6.866, 81.046),
    ("Galle Dutch Fort", "culture", "Historic beautifully preserved 17th-century coastal fortress.", "Galle", 6.028, 80.217),
    ("Nuwara Eliya Tea Gardens", "nature", "Lush green rolling hills spanning iconic Ceylon tea estates.", "Nuwara Eliya", 6.949, 80.783),
    ("Pinnawala Elephant Orphanage", "wildlife", "Nursery and captive breeding ground for wild Asian elephants.", "Kegalle", 7.301, 80.387),
    ("Arugam Bay Surf Point", "adventure", "World-renowned surfing destination with perfect right-hand breaks.", "Arugam Bay", 6.843, 81.826),
    ("Dambulla Cave Temple", "culture", "Largest and best-preserved cave temple complex in Sri Lanka.", "Dambulla", 7.856, 80.648)
]

for name, cat, desc, q, lat, lng in FAMOUS:
    places.append({
        "name": name,
        "category": cat,
        "description": desc,
        "search_query": f"{name} {q} Sri Lanka",
        "lat": lat,
        "lng": lng
    })
    place_names.add(name)

# Auto-generate the rest to reach 150 accurately
random.seed(42) # Deterministic
while len(places) < 150:
    city = random.choice(CITIES)
    cat_id, flavors = random.choice(CATEGORIES)
    flavor = random.choice(flavors)
    
    # E.g. "Colombo Temple" or "Kandy Mountain Viewpoint"
    name = f"{city['city']} {flavor}"
    if name in place_names:
        # Try a variant
        name = f"Hidden {flavor} of {city['city']}"
        if name in place_names:
            name = f"Grand {city['city']} {flavor}"
            
    if name not in place_names:
        place_names.add(name)
        lat_offset = random.uniform(-0.05, 0.05)
        lng_offset = random.uniform(-0.05, 0.05)
        places.append({
            "name": name,
            "category": cat_id,
            "description": f"A notable {flavor.lower()} located in the vibrant area of {city['city']}, highlighting the {cat_id} of the region.",
            "search_query": f"{name} Sri Lanka",
            "lat": round(city["base_lat"] + lat_offset, 5),
            "lng": round(city["base_lng"] + lng_offset, 5)
        })

py_code = f'# AUTO-GENERATED FALLBACK DATA\nFALLBACK_PLACES = {json.dumps(places, indent=4)}\n'

import os
os.makedirs('services', exist_ok=True)
with open('services/fallback_data.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

print(f"Successfully generated {len(places)} places into services/fallback_data.py")
