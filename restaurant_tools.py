import requests
from langchain_core.tools import tool


# Public Overpass API servers.
# If one fails or times out, we try the next one.
OVERPASS_URLS = [
    # "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]
@tool
def get_location_coordinates(place_name: str) -> dict:
    """
    Convert a place name into latitude and longitude.

    Example:
        "KL Sentral, Kuala Lumpur"
        → latitude and longitude
    """

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": "AI-Dining-Assistant/1.0"
    }

    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return {
                "error": f"Location '{place_name}' not found."
            }

        location = results[0]

        return {
            "place": location.get("display_name"),
            "latitude": float(location["lat"]),
            "longitude": float(location["lon"])
        }

    except requests.RequestException as e:
        return {
            "error": f"Geocoding failed: {str(e)}"
        }
@tool
def find_restaurants(
    latitude: float,
    longitude: float,
    radius: int = 3000
) -> list:
    """
    Find current restaurants near a geographic location using OpenStreetMap.

    Args:
        latitude: Latitude of the search location.
        longitude: Longitude of the search location.
        radius: Search radius in meters.

    Returns:
        A list of restaurants with available information such as
        name, cuisine, opening hours, phone, website and coordinates.
    """

    query = f"""
    [out:json][timeout:25];

    (
      node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
      way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
      relation["amenity"="restaurant"](around:{radius},{latitude},{longitude});
    );

    out center tags;
    """

    headers = {
        "User-Agent": "AI-Dining-Assistant/1.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = None

    # Try available Overpass servers
    for url in OVERPASS_URLS:
        try:
            print(f"Trying: {url}")

            response = requests.post(
                url,
                data={"data": query},
                headers=headers,
                timeout=60,
            )

            response.raise_for_status()
            break

        except requests.RequestException as e:
            print(f"Failed: {e}")
            response = None

    if response is None:
        return [{
            "error": "Unable to retrieve restaurant data from OpenStreetMap."
        }]

    data = response.json()

    restaurants = []

    for place in data.get("elements", []):
        tags = place.get("tags", {})

        name = tags.get("name")

        # Ignore unnamed restaurant entries
        if not name:
            continue

        restaurant = {
            "name": name,
            "cuisine": tags.get("cuisine", "Unknown"),
            "opening_hours": tags.get("opening_hours", "Unknown"),
            "phone": tags.get(
                "phone",
                tags.get("contact:phone", "Unknown")
            ),
            "website": tags.get(
                "website",
                tags.get("contact:website", "Unknown")
            ),
            "latitude": place.get(
                "lat",
                place.get("center", {}).get("lat")
            ),
            "longitude": place.get(
                "lon",
                place.get("center", {}).get("lon")
            ),
        }

        restaurants.append(restaurant)

    return restaurants