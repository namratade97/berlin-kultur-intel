from geopy.geocoders import Nominatim
from qdrant_client import QdrantClient
import time

client = QdrantClient("http://localhost:6333")
geolocator = Nominatim(user_agent="berlin_event_agent")

# Coordinates for "Various venues" fallback
BERLIN_CENTER = {"lat": 52.5200, "lng": 13.4050} # Berlin Center

def get_coords(venue, district):
    if "various" in venue.lower() or not venue:
        print(f"Various venues detected for {district}, using center fallback.")
        return BERLIN_CENTER["lat"], BERLIN_CENTER["lng"]
    
    try:
        query = f"{venue}, {district}, Berlin, Germany"
        location = geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude
        return BERLIN_CENTER["lat"], BERLIN_CENTER["lng"]
    except Exception as e:
        print(f"Geocoding error: {e}")
        return BERLIN_CENTER["lat"], BERLIN_CENTER["lng"]

def update_qdrant_with_coords():
    # 1. Fetching all points
    scroll_result = client.scroll(collection_name="berlin_events", limit=100, with_payload=True)
    points = scroll_result[0]

    for point in points:
        payload = point.payload
        venue = payload.get("venueName", "")
        district = payload.get("district", "Berlin")
        
        lat, lng = get_coords(venue, district)
        
        # 2. Updating payload with new fields
        payload["lat"] = lat
        payload["lng"] = lng
        
        # 3. Overwriting in Qdrant
        client.overwrite_payload(
            collection_name="berlin_events",
            payload=payload,
            points=[point.id]
        )
        print(f"Updated {payload['eventName']} at {lat}, {lng}")
        time.sleep(1)

if __name__ == "__main__":
    update_qdrant_with_coords()