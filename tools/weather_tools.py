import requests
import json
import time
from typing import Dict, Any, Optional

_weather_cache: Dict[str, Any] = {}
_cache_time: float = 0

def get_weather(city: str = "auto") -> str:
    """
    Fetches real-time atmospheric and meteorological conditions.
    Uses free, zero-key endpoints (Open-Meteo / wttr.in) with local memory caching.
    """
    global _weather_cache, _cache_time

    # Return cached weather if within 15 minutes
    if _weather_cache and (time.time() - _cache_time < 900) and city == "auto":
        return _format_weather(_weather_cache)

    try:
        # Use wttr.in JSON format (automatically geolocates if city="auto")
        target = "" if city == "auto" else city
        url = f"https://wttr.in/{target}?format=j1"
        resp = requests.get(url, timeout=4.0, headers={"User-Agent": "curl/7.68.0"})
        if resp.status_code == 200:
            data = resp.json()
            _weather_cache = data
            _cache_time = time.time()
            return _format_weather(data)
    except Exception:
        pass

    # Offline / Cache Fallback
    if _weather_cache:
        return _format_weather(_weather_cache) + " (from recent telemetry cache)"

    return "Atmospheric sensors are currently offline, sir. Unable to retrieve current meteorological data."

def _format_weather(data: Dict[str, Any]) -> str:
    try:
        curr = data["current_condition"][0]
        temp_c = curr.get("temp_C", "N/A")
        feels_c = curr.get("FeelsLikeC", "N/A")
        desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
        humidity = curr.get("humidity", "N/A")
        wind = curr.get("windspeedKmph", "N/A")

        area = "Local Area"
        nearest = data.get("nearest_area", [])
        if nearest:
            area = nearest[0].get("areaName", [{}])[0].get("value", "Local Area")

        return (
            f"Atmospheric conditions in {area}: {desc}. "
            f"Temperature is {temp_c}°C (feels like {feels_c}°C), "
            f"with humidity at {humidity}% and wind speeds of {wind} km/h, sir."
        )
    except Exception:
        return "Meteorological telemetry is currently unavailable, sir."
