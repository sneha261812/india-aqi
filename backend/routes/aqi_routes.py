"""
routes/aqi_routes.py
AQI data endpoints.
"""

from flask import Blueprint, jsonify, request
from db import get_supabase
import logging

logger = logging.getLogger(__name__)
aqi_bp = Blueprint("aqi", __name__)


@aqi_bp.route("/current/<city>", methods=["GET"])
def current_city(city):
    """Latest AQI reading for a single city."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("*")
            .eq("city", city)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return jsonify({"error": f"No data for {city}"}), 404
        return jsonify(result.data[0])
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal server error"}), 500


@aqi_bp.route("/all", methods=["GET"])
def all_cities():
    """Latest AQI for all monitored cities (one row per city)."""
    try:
        sb = get_supabase()
        # Fetch recent readings and deduplicate by city client-side
        result = (
            sb.table("aqi_readings")
            .select("city, aqi, pm25, pm10, timestamp, lat, lon, source")
            .order("timestamp", desc=True)
            .limit(200)
            .execute()
        )
        seen, latest = set(), []
        for row in result.data:
            if row["city"] not in seen:
                seen.add(row["city"])
                latest.append(row)
        return jsonify(latest)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal server error"}), 500


@aqi_bp.route("/history/<city>", methods=["GET"])
def history(city):
    """Historical AQI for a city. Optional ?days=N (default 30)."""
    days = request.args.get("days", 30, type=int)
    days = min(days, 365)
    try:
        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("timestamp, aqi, pm25, pm10, no2, so2, o3, co")
            .eq("city", city)
            .gte("timestamp", since)
            .order("timestamp", desc=False)
            .execute()
        )
        return jsonify({"city": city, "days": days, "data": result.data})
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal server error"}), 500


@aqi_bp.route("/alerts", methods=["GET"])
def alerts():
    """Recent unresolved AQI alerts."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_alerts")
            .select("*")
            .eq("resolved", False)
            .order("timestamp", desc=True)
            .limit(50)
            .execute()
        )
        return jsonify(result.data)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal server error"}), 500
