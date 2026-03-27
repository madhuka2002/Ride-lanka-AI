import urllib.request
import json

req = urllib.request.Request(
    'http://localhost:8000/api/ai/culture-info',
    data=json.dumps({"place_name":"Sigiriya"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode('utf-8'))
except Exception as e:
    if hasattr(e, 'read'):
        print("HTTP ERROR:", e.code, e.read().decode('utf-8'))
    else:
        print("FATAL ERROR:", e)
