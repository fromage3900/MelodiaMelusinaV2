"""Simple test client simulating UE: sends a rank_layouts request to local service."""
import requests

PAYLOAD = {
    "job_type": "rank_layouts",
    "seed": 42,
    "candidates": [
        {"id": "A", "difficulty": 0.7, "spacing": 0.4},
        {"id": "B", "difficulty": 0.8, "spacing": 0.6},
        {"id": "C", "difficulty": 0.6, "spacing": 0.5},
    ],
}

if __name__ == "__main__":
    url = "http://127.0.0.1:8008/rank_layouts"
    r = requests.post(url, json=PAYLOAD, timeout=10)
    print("status", r.status_code)
    print(r.json())
