import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_phase4():
    # 0. Register Users with unique emails
    suffix = str(int(time.time()))[-6:]
    email_d = f"d{suffix}@test.com"
    email_p = f"p{suffix}@test.com"
    
    print(f"Test Users: {email_d}, {email_p}")
    reg_d = requests.post(f"{BASE_URL}/auth/register", json={"email": email_d, "password": "password123", "name": f"Driver {suffix}", "role": "driver"})
    reg_p = requests.post(f"{BASE_URL}/auth/register", json={"email": email_p, "password": "password123", "name": f"Pass {suffix}", "role": "passenger"})

    # 1. Login Driver
    driver_login = requests.post(f"{BASE_URL}/auth/login", json={"email": email_d, "password": "password123"})
    driver_token = driver_login.json()["access_token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # 2. Login Passenger
    pass_login = requests.post(f"{BASE_URL}/auth/login", json={"email": email_p, "password": "password123"})
    pass_token = pass_login.json()["access_token"]
    pass_headers = {"Authorization": f"Bearer {pass_token}"}

    # 3. Create a Ride (3 seats)
    polyline_data = json.dumps([
        {"latitude": 12.0, "longitude": 12.0},
        {"latitude": 12.5, "longitude": 12.5},
        {"latitude": 13.0, "longitude": 13.0}
    ])
    
    ride_data = {
        "origin": "Main Gate",
        "destination": "Academic Block",
        "departure_time": "2026-03-10T10:00:00",
        "seats_available": 3,
        "price": 100.0,
        "origin_lat": 12.0,
        "origin_lng": 12.0,
        "destination_lat": 13.0,
        "destination_lng": 13.0,
        "route_polyline": polyline_data,
        "checkpoints": []
    }
    ride_res = requests.post(f"{BASE_URL}/rides/", json=ride_data, headers=driver_headers)
    if ride_res.status_code != 200:
        print(f"Ride Creation Error: {ride_res.text}")
        return
    ride_id = ride_res.json()["id"]
    print(f"Created Ride {ride_id} with 3 seats.")

    # 4. Search Ride (Verify Suggested Price)
    search_res = requests.get(f"{BASE_URL}/rides/?pickup_lat=12.0&pickup_lng=12.0&dest_lat=12.5&dest_lng=12.5", headers=pass_headers)
    rides_found = search_res.json()
    ride_found = [r for r in rides_found if r["id"] == ride_id]
    if not ride_found:
        print("Ride not found in search results.")
        return
    
    print(f"Suggested Price for half route: {ride_found[0].get('suggested_price')}")

    # 5. Request 2 Seats
    req_data = {
        "ride_id": ride_id,
        "num_seats": 2,
        "origin": "Gate 1",
        "destination": "Midpoint"
    }
    req_res = requests.post(f"{BASE_URL}/requests/", json=req_data, headers=pass_headers)
    if req_res.status_code != 200:
        print(f"Request Creation Error: {req_res.status_code} - {req_res.text}")
        return
    req_id = req_res.json()["id"]
    print(f"Requested 2 seats. Request ID: {req_id}")

    # 6. Accept Request (Driver)
    requests.put(f"{BASE_URL}/requests/{req_id}/accept", headers=driver_headers)
    print("Driver accepted request.")

    # 7. Confirm Request (Passenger)
    requests.put(f"{BASE_URL}/requests/{req_id}/confirm", headers=pass_headers)
    print("Passenger confirmed ride.")

    # 8. Verify Seats (Should be 1 left)
    ride_verify = requests.get(f"{BASE_URL}/rides/my-rides", headers=driver_headers)
    ride_obj = [r for r in ride_verify.json()["created"] if r["id"] == ride_id][0]
    print(f"Seats Available After Confirmation: {ride_obj['seats_available']}")

    # 9. Cancel Request & Verify Seats (Should be 3 again)
    requests.put(f"{BASE_URL}/requests/{req_id}/cancel", headers=pass_headers)
    ride_verify2 = requests.get(f"{BASE_URL}/rides/my-rides", headers=driver_headers)
    ride_obj2 = [r for r in ride_verify2.json()["created"] if r["id"] == ride_id][0]
    print(f"Seats Available After Cancellation: {ride_obj2['seats_available']}")

    # 10. Re-confirm and then Complete Ride (Verify Stats)
    requests.post(f"{BASE_URL}/requests/", json=req_data, headers=pass_headers) # New request
    new_req_id = requests.get(f"{BASE_URL}/requests/passenger", headers=pass_headers).json()[-1]["id"]
    requests.put(f"{BASE_URL}/requests/{new_req_id}/accept", headers=driver_headers)
    requests.put(f"{BASE_URL}/requests/{new_req_id}/confirm", headers=pass_headers)
    
    requests.put(f"{BASE_URL}/rides/{ride_id}/complete", headers=driver_headers)
    print("Ride completed.")

    # Verify Driver Stats
    driver_profile = requests.get(f"{BASE_URL}/auth/me", headers=driver_headers)
    print(f"Driver Rides Given: {driver_profile.json().get('rides_given')}")

if __name__ == "__main__":
    try:
        test_phase4()
    except Exception as e:
        import traceback
        traceback.print_exc()
