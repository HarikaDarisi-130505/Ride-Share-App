import requests
import time
import os

BASE_URL = os.getenv("TEST_API_BASE_URL", "https://ride-share-app-production-ab31.up.railway.app").rstrip("/")

def test_api():
    print("Starting API tests...")
    
    # 1. Register/Login users
    driver_data = {
        "email": "driver@test.com", "password": "password123",
        "full_name": "Test Driver", "phone": "1234567890", "role": "driver"
    }
    passenger_data = {
        "email": "passenger@test.com", "password": "password123",
        "full_name": "Test Passenger", "phone": "0987654321", "role": "passenger"
    }
    
    # Try creating or just login
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": driver_data['email'], 
        "password": driver_data['password'],
        "name": driver_data['full_name'],
        "role": driver_data['role']
    })
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": passenger_data['email'], 
        "password": passenger_data['password'],
        "name": passenger_data['full_name'],
        "role": passenger_data['role']
    })
    
    # Login Driver
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": driver_data['email'], "password": driver_data['password']})
    if r.status_code != 200:
        print(f"Driver login failed: {r.text}")
        return
    driver_token = r.json().get('access_token')
    
    # Login Passenger
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": passenger_data['email'], "password": passenger_data['password']})
    if r.status_code != 200:
        print(f"Passenger login failed: {r.text}")
        return
    pass_token = r.json().get('access_token')
    
    driver_headers = {"Authorization": f"Bearer {driver_token}"}
    pass_headers = {"Authorization": f"Bearer {pass_token}"}
    
    # 2. Driver creates a ride
    ride_data = {
        "origin": "Location A", "destination": "Location B",
        "origin_lat": 10.0, "origin_lng": 10.0,
        "destination_lat": 20.0, "destination_lng": 20.0,
        "departure_time": "2026-10-10T10:00:00",
        "seats_available": 3, "price": 100.0,
        "route_polyline": "[]", "checkpoints": []
    }
    r = requests.post(f"{BASE_URL}/rides/", json=ride_data, headers=driver_headers)
    if r.status_code != 200:
        print(f"Failed to create ride: {r.text}")
        return
    ride_id = r.json()['id']
    print(f"Created Ride ID: {ride_id}")
    
    # 3. Passenger gets rides (Phase 1)
    r = requests.get(f"{BASE_URL}/rides/", headers=pass_headers)
    if r.status_code == 200:
        print("Passenger get rides successful")
    else:
        print(f"Passenger get rides failed: {r.text}")
        
    # 4. Passenger requests ride (Phase 2)
    req_data = {"ride_id": ride_id, "origin": "Start", "destination": "End"}
    r = requests.post(f"{BASE_URL}/requests/", json=req_data, headers=pass_headers)
    if r.status_code != 200:
        print(f"Passenger request failed: {r.text}")
        return
    req_id = r.json()['id']
    print(f"Created Request ID: {req_id}")
    
    # Passenger shouldn't be able to request again
    r = requests.post(f"{BASE_URL}/requests/", json=req_data, headers=pass_headers)
    if r.status_code == 400 and "pending ride request" in r.text:
        print("Single active request rule working!")
    else:
        print(f"Single active rule failed: {r.text}")
        
    # 5. Driver accepts request (Phase 3)
    r = requests.put(f"{BASE_URL}/requests/{req_id}/accept", headers=driver_headers)
    if r.status_code == 200 and r.json()['status'] == 'accepted':
        print("Driver successfully accepted request")
    else:
        print(f"Driver accept failed: {r.text}")
        
    # 6. Passenger confirms request (Phase 3)
    r = requests.put(f"{BASE_URL}/requests/{req_id}/confirm", headers=pass_headers)
    if r.status_code == 200 and r.json()['status'] == 'confirmed':
        print("Passenger successfully confirmed request")
    else:
        print(f"Passenger confirm failed: {r.text}")
        
    print("API tests completed.")

if __name__ == '__main__':
    test_api()
