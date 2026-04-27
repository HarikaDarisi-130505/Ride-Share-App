
import requests
import json

def test_nominatim():
    url = "https://nominatim.openstreetmap.org/reverse?lat=16.4957&lon=80.4991&format=json&addressdetails=1&accept-language=en"
    headers = {'User-Agent': 'RideShareVITAP-Test'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_nominatim()
