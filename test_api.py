import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://localhost:8000/api/ai/recommend',
    data=json.dumps({"user_id":"test", "interests":[], "behavior_queue":[]}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("FATAL ERROR:", e)
