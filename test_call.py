"""Simple local test to POST /call to the FastAPI server.

Run after starting the server with:
    uvicorn backend.server:app --reload --app-dir developersdens_assignment
"""
import requests
import json

URL = "http://localhost:8000/call"

payload = {
    "phone_number": "+16626232013",
    "customer_name": "Ali",
    "sip_trunk_id": None,
}

resp = requests.post(URL, json=payload, timeout=30)
print(resp.status_code)
print(json.dumps(resp.json(), indent=2))
