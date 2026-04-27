
import requests

def get_coords(query):
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
    headers = {'User-Agent': 'RideShareVITAP-StudentProject/1.0'}
    resp = requests.get(url, headers=headers)
    if resp.ok and resp.json():
        p = resp.json()[0]
        return float(p['lat']), float(p['lon'])
    return None

pamuru = get_coords("Pamuru, Andhra Pradesh")
vijayawada = get_coords("Vijayawada, Andhra Pradesh")

print(f"Pamuru: {pamuru}")
print(f"Vijayawada: {vijayawada}")
