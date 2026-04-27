
import requests
import json

BASE_URL = "http://localhost:8000" # Ensure your backend is running

def test_registration_flow():
    email = "otp_test_6@example.com"
    phone = "1234567890"
    
    print(f"--- Testing Registration for {email} ---")
    
    # 1. Register
    reg_data = {
        "name": "OTP Tester",
        "email": email,
        "password": "password123",
        "phone_number": phone
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
        print(f"Register Status: {response.status_code}")
        print(f"Register Response: {response.json()}")
        
        if response.status_code != 200:
            return

        # Note: You need to check the backend console for the printed OTP!
        # In a real test, we might use a mock that returns the OTP.
        # Here we'll just wait for the user to check logs if they were running it.
        # But for this automated script, it will fail unless the backend is running.
        
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    test_registration_flow()
