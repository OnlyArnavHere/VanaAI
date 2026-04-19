"""Quick test script for the VanaAI analysis endpoint."""
import httpx
import json
import sys

try:
    r = httpx.post(
        "http://localhost:8000/api/analyze",
        json={"latitude": 19.076, "longitude": 72.877, "radius_meters": 500},
        timeout=60,
    )
    print(f"Status: {r.status_code}")
    data = r.json()
    print(json.dumps(data, indent=2)[:4000])
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
