import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("")
async def get_weather(lat: float = None, lon: float = None, city: str = None, unit: str = "fahrenheit"):
    """
    Fetch current weather using Open-Meteo (free, no API key needed).
    Supports: lat/lon coordinates OR city name search OR "my location" for geolocation.
    Use ?unit=celsius for Celsius, ?unit=fahrenheit (default) for Fahrenheit.
    """
    if city:
        # Geocode city name
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(geo_url)
            resp.raise_for_status()
            geo_data = resp.json()
        results = geo_data.get("results", [])
        if not results:
            return {"error": f"City '{city}' not found"}
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        location_name = results[0].get("name", city)
    elif lat is None or lon is None:
        # Default to Berlin if no location provided
        lat = 52.52
        lon = 13.41
        location_name = "Berlin"
    else:
        location_name = "Current Location"

    # Determine units
    use_fahrenheit = unit.lower() in ("fahrenheit", "f", "imperial")
    temp_unit = "fahrenheit" if use_fahrenheit else "celsius"
    wind_unit = "mph" if use_fahrenheit else "mph"  # Open-Meteo uses mph for both when using imperial

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,weather_code,"
        "wind_speed_10m,relative_humidity_2m,precipitation"
        f"&temperature_unit={temp_unit}"
        f"&wind_speed_unit={wind_unit}"
        "&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    current = data["current"]

    # Map WMO weather codes to a human-readable description + emoji
    code = current.get("weather_code", 0)
    description, emoji = _wmo_description(code)

    temp = current["temperature_2m"]
    feels_like = current["apparent_temperature"]
    unit_symbol = "°F" if use_fahrenheit else "°C"

    return {
        "temperature": temp,
        "feels_like": feels_like,
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "precipitation": current["precipitation"],
        "description": description,
        "emoji": emoji,
        "unit": unit_symbol,
        "timezone": data.get("timezone", ""),
        "location": location_name,
    }


def _wmo_description(code: int) -> tuple[str, str]:
    table = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Icy fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌦️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        71: ("Slight snow", "❄️"),
        73: ("Moderate snow", "❄️"),
        75: ("Heavy snow", "❄️"),
        77: ("Snow grains", "❄️"),
        80: ("Slight showers", "🌦️"),
        81: ("Moderate showers", "🌧️"),
        82: ("Violent showers", "⛈️"),
        85: ("Slight snow showers", "🌨️"),
        86: ("Heavy snow showers", "🌨️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm + hail", "⛈️"),
        99: ("Thunderstorm + heavy hail", "⛈️"),
    }
    return table.get(code, ("Unknown", "🌡️"))
