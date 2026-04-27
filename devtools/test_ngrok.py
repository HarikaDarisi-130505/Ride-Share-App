import requests
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.config import PUBLIC_API_BASE_URL

def test_ngrok():
    url = f"{PUBLIC_API_BASE_URL}/auth/login"
    data = {
        "email": "fresh@example.com",
        "password": "password123"
    }
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ngrok()
