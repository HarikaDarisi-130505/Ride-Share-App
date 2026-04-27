import requests

def test_ride_creation():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Login
    login_data = {"email": "fresh@example.com", "password": "password123"}
    login_res = requests.post(f"{base_url}/auth/login", json=login_data)
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create Ride
    ride_data = {
        "origin": "Main Gate",
        "destination": "Academic Block",
        "departure_time": "2026-02-22T10:00:00",
        "seats_available": 3,
        "origin_lat": 12.9716,
        "origin_lng": 77.5946,
        "destination_lat": 12.9720,
        "destination_lng": 77.5950,
        "price": 50.0,
        "route_polyline": "encoded_polyline_here",
        "checkpoints": [
            {"latitude": 12.9718, "longitude": 77.5948, "address": "Midway", "stop_order": 1}
        ]
    }
    
    try:
        response = requests.post(f"{base_url}/rides/", json=ride_data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_ride_creation()
