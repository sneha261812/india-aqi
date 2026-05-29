"""
services/anomaly.py
Detects AQI spikes and stores alerts in Supabase.
"""

import logging
from datetime import datetime, timezone
from db import get_supabase

logger = logging.getLogger(__name__)

# Thresholds for anomaly detection
SPIKE_THRESHOLD   = 200   # AQI above this triggers a spike alert
HAZARDOUS_LEVEL   = 300   # AQI above this is "hazardous"
SURGE_DELTA       = 75    # AQI rise > this from prior reading triggers surge alert


def _get_last_aqi(city: str) -> int | None:
    """Retrieve the most recent AQI reading for a city (excluding current)."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("aqi")
            .eq("city", city)
            .order("timestamp", desc=True)
            .limit(2)
            .execute()
        )
        rows = result.data
        if len(rows) >= 2:
            return rows[1]["aqi"]
        return None
    except Exception as exc:
        logger.warning(f"Could not fetch last AQI for {city}: {exc}")
        return None


def detect_anomaly(record: dict):
    """Check record for anomalies and persist alerts if found."""
    city    = record["city"]
    current = record.get("aqi", 0)
    alerts  = []

    if current >= HAZARDOUS_LEVEL:
        alerts.append({"type": "hazardous", "message": f"Hazardous AQI {current} detected in {city}"})
    elif current >= SPIKE_THRESHOLD:
        alerts.append({"type": "spike", "message": f"High AQI spike {current} in {city}"})

    prev = _get_last_aqi(city)
    if prev and (current - prev) >= SURGE_DELTA:
        alerts.append({
            "type":    "surge",
            "message": f"Rapid AQI surge in {city}: {prev} → {current} (+{current - prev})"
        })

    if not alerts:
        return

    sb = get_supabase()
    for alert in alerts:
        try:
            sb.table("aqi_alerts").insert({
                "city":       city,
                "aqi":        current,
                "alert_type": alert["type"],
                "message":    alert["message"],
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "resolved":   False,
            }).execute()
            logger.warning(f"🚨 Alert [{alert['type']}]: {alert['message']}")
        except Exception as exc:
            logger.error(f"Failed to save alert: {exc}")
