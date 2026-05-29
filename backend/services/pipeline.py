"""
services/pipeline.py
Full AQI ingestion pipeline:
  WAQI → OpenAQ fallback → Open-Meteo weather enrichment
  → validation → dedup → Supabase insert → anomaly check
"""

import os
import time
import logging
from datetime import datetime, timezone
import requests
from db import get_supabase

logger = logging.getLogger(__name__)

WAQI_TOKEN  = os.getenv("WAQI_API_TOKEN")
WAQI_BASE   = "https://api.waqi.info"
OPENAQ_BASE = "https://api.openaq.org/v2"
METEO_BASE  = "https://api.open-meteo.com/v1/forecast"

# City → approximate lat/lon (used for weather enrichment)
CITY_COORDS: dict[str, tuple[float, float]] = {
    "Delhi":          (28.6139, 77.2090),
    "Mumbai":         (19.0760, 72.8777),
    "Bangalore":      (12.9716, 77.5946),
    "Hyderabad":      (17.3850, 78.4867),
    "Chennai":        (13.0827, 80.2707),
    "Kolkata":        (22.5726, 88.3639),
    "Pune":           (18.5204, 73.8567),
    "Ahmedabad":      (23.0225, 72.5714),
    "Jaipur":         (26.9124, 75.7873),
    "Lucknow":        (26.8467, 80.9462),
    "Kanpur":         (26.4499, 80.3319),
    "Nagpur":         (21.1458, 79.0882),
    "Indore":         (22.7196, 75.8577),
    "Thane":          (19.2183, 72.9781),
    "Bhopal":         (23.2599, 77.4126),
    "Visakhapatnam":  (17.6868, 83.2185),
    "Vadodara":       (22.3072, 73.1812),
    "Patna":          (25.5941, 85.1376),
    "Ludhiana":       (30.9010, 75.8573),
    "Agra":           (27.1767, 78.0081),
    "Nashik":         (19.9975, 73.7898),
    "Faridabad":      (28.4089, 77.3178),
    "Meerut":         (28.9845, 77.7064),
    "Rajkot":         (22.3039, 70.8022),
    "Varanasi":       (25.3176, 82.9739),
    "Srinagar":       (34.0837, 74.7973),
    "Aurangabad":     (19.8762, 75.3433),
    "Dhanbad":        (23.7957, 86.4304),
    "Amritsar":       (31.6340, 74.8723),
    "Allahabad":      (25.4358, 81.8463),
    "Ranchi":         (23.3441, 85.3096),
    "Coimbatore":     (11.0168, 76.9558),
    "Vijayawada":     (16.5062, 80.6480),
    "Jodhpur":        (26.2389, 73.0243),
    "Madurai":        (9.9252, 78.1198),
    "Raipur":         (21.2514, 81.6296),
    "Kota":           (25.2138, 75.8648),
    "Chandigarh":     (30.7333, 76.7794),
    "Guwahati":       (26.1445, 91.7362),
    "Solapur":        (17.6805, 75.9064),
}


# ── WAQI ───────────────────────────────────────────────────────────────────

def fetch_waqi(city: str) -> dict | None:
    """Fetch current AQI from WAQI for a given city."""
    try:
        url = f"{WAQI_BASE}/feed/{city.lower()}/?token={WAQI_TOKEN}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            return None
        d = data["data"]
        aqi = d.get("aqi")
        if not isinstance(aqi, (int, float)) or aqi < 0:
            return None
        iaqi = d.get("iaqi", {})
        return {
            "city":      city,
            "aqi":       int(aqi),
            "station":   d.get("city", {}).get("name", city),
            "lat":       d.get("city", {}).get("geo", [None, None])[0],
            "lon":       d.get("city", {}).get("geo", [None, None])[1],
            "pm25":      iaqi.get("pm25", {}).get("v"),
            "pm10":      iaqi.get("pm10", {}).get("v"),
            "no2":       iaqi.get("no2",  {}).get("v"),
            "so2":       iaqi.get("so2",  {}).get("v"),
            "co":        iaqi.get("co",   {}).get("v"),
            "o3":        iaqi.get("o3",   {}).get("v"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source":    "waqi",
        }
    except Exception as exc:
        logger.warning(f"WAQI fetch failed for {city}: {exc}")
        return None


# ── OpenAQ fallback ────────────────────────────────────────────────────────

def fetch_openaq(city: str) -> dict | None:
    """Fallback to OpenAQ v2 for a city when WAQI fails."""
    try:
        params = {"city": city, "country": "IN", "limit": 5, "order_by": "lastUpdated", "sort": "desc"}
        resp = requests.get(f"{OPENAQ_BASE}/locations", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        loc = results[0]
        params_data = {p["parameter"]: p["lastValue"] for p in loc.get("parameters", [])}
        pm25 = params_data.get("pm25")
        pm10 = params_data.get("pm10")
        # Rough AQI estimate from PM2.5 when direct AQI not available
        aqi_estimate = _pm25_to_aqi(pm25) if pm25 else None
        if not aqi_estimate:
            return None
        coords = loc.get("coordinates", {})
        return {
            "city":      city,
            "aqi":       aqi_estimate,
            "station":   loc.get("name", city),
            "lat":       coords.get("latitude"),
            "lon":       coords.get("longitude"),
            "pm25":      pm25,
            "pm10":      pm10,
            "no2":       params_data.get("no2"),
            "so2":       params_data.get("so2"),
            "co":        params_data.get("co"),
            "o3":        params_data.get("o3"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source":    "openaq",
        }
    except Exception as exc:
        logger.warning(f"OpenAQ fetch failed for {city}: {exc}")
        return None


def _pm25_to_aqi(pm25: float) -> int | None:
    """Simple linear AQI estimate from PM2.5 µg/m³ (US EPA breakpoints)."""
    breakpoints = [
        (0.0,  12.0,   0,  50),
        (12.1, 35.4,  51, 100),
        (35.5, 55.4, 101, 150),
        (55.5,150.4, 151, 200),
        (150.5,250.4,201, 300),
        (250.5,350.4,301, 400),
        (350.5,500.4,401, 500),
    ]
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= pm25 <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (pm25 - c_lo) + i_lo)
    return None


# ── Weather enrichment ─────────────────────────────────────────────────────

def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather features from Open-Meteo (free, no key)."""
    try:
        params = {
            "latitude":  lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "relativehumidity_2m,windspeed_10m,precipitation",
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }
        resp = requests.get(METEO_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cw = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        # Take first hour's humidity / precipitation
        return {
            "temperature":    cw.get("temperature"),
            "windspeed":      cw.get("windspeed"),
            "winddirection":  cw.get("winddirection"),
            "humidity":       (hourly.get("relativehumidity_2m") or [None])[0],
            "precipitation":  (hourly.get("precipitation")       or [None])[0],
        }
    except Exception as exc:
        logger.warning(f"Weather fetch failed ({lat},{lon}): {exc}")
        return {}


# ── Deduplication ──────────────────────────────────────────────────────────

def is_duplicate(city: str, timestamp: str) -> bool:
    """Return True if a record for this city exists within the last 10 minutes."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("id")
            .eq("city", city)
            .gte("timestamp", timestamp[:16])   # match to the minute
            .execute()
        )
        return len(result.data) > 0
    except Exception:
        return False


# ── Supabase insert ────────────────────────────────────────────────────────

def save_reading(record: dict) -> bool:
    """Insert one AQI reading into Supabase."""
    try:
        sb = get_supabase()
        sb.table("aqi_readings").insert(record).execute()
        return True
    except Exception as exc:
        logger.error(f"Supabase insert failed for {record.get('city')}: {exc}")
        return False


# ── Anomaly trigger ────────────────────────────────────────────────────────

def check_and_store_anomaly(record: dict):
    from services.anomaly import detect_anomaly
    detect_anomaly(record)


# ── Main pipeline ──────────────────────────────────────────────────────────

def ingest_city(city: str):
    logger.info(f"Ingesting {city} …")

    # 1. Fetch AQI
    data = fetch_waqi(city)
    if not data:
        logger.info(f"  WAQI failed — trying OpenAQ for {city}")
        data = fetch_openaq(city)
    if not data:
        logger.warning(f"  Both sources failed for {city}. Skipping.")
        return

    # 2. Weather enrichment
    lat = data.get("lat") or CITY_COORDS.get(city, (None, None))[0]
    lon = data.get("lon") or CITY_COORDS.get(city, (None, None))[1]
    if lat and lon:
        weather = fetch_weather(lat, lon)
        data.update(weather)

    # 3. Dedup
    if is_duplicate(city, data["timestamp"]):
        logger.info(f"  Duplicate — skipping {city}")
        return

    # 4. Save
    saved = save_reading(data)
    if saved:
        logger.info(f"  ✅ Saved {city} AQI={data['aqi']}")

    # 5. Anomaly check (non-blocking)
    try:
        check_and_store_anomaly(data)
    except Exception:
        pass


def ingest_all_cities(cities: list[str]):
    for city in cities:
        try:
            ingest_city(city)
            time.sleep(0.4)   # be polite to WAQI rate limits
        except Exception as exc:
            logger.error(f"Unhandled error for {city}: {exc}", exc_info=True)
    logger.info("✅ Ingestion cycle complete")
