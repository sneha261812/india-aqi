"""
routes/state_routes.py
State-level AQI aggregation endpoints.
"""

from flask import Blueprint, jsonify
from db import get_supabase
import logging

logger = logging.getLogger(__name__)
state_bp = Blueprint("states", __name__)

# Map each city to its state
CITY_STATE_MAP = {
    "Delhi": "Delhi", "Faridabad": "Haryana", "Gurgaon": "Haryana",
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Nagpur": "Maharashtra",
    "Nashik": "Maharashtra", "Thane": "Maharashtra", "Aurangabad": "Maharashtra",
    "Solapur": "Maharashtra",
    "Bangalore": "Karnataka",
    "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu", "Coimbatore": "Tamil Nadu", "Madurai": "Tamil Nadu",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat", "Vadodara": "Gujarat", "Rajkot": "Gujarat",
    "Jaipur": "Rajasthan", "Jodhpur": "Rajasthan", "Kota": "Rajasthan",
    "Lucknow": "Uttar Pradesh", "Kanpur": "Uttar Pradesh", "Agra": "Uttar Pradesh",
    "Varanasi": "Uttar Pradesh", "Meerut": "Uttar Pradesh", "Allahabad": "Uttar Pradesh",
    "Patna": "Bihar",
    "Bhopal": "Madhya Pradesh", "Indore": "Madhya Pradesh",
    "Visakhapatnam": "Andhra Pradesh", "Vijayawada": "Andhra Pradesh",
    "Chandigarh": "Chandigarh", "Ludhiana": "Punjab", "Amritsar": "Punjab",
    "Srinagar": "Jammu & Kashmir",
    "Ranchi": "Jharkhand", "Dhanbad": "Jharkhand",
    "Raipur": "Chhattisgarh",
    "Guwahati": "Assam",
}


@state_bp.route("/", methods=["GET"])
def all_states():
    """Return average AQI per state (latest readings)."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("city, aqi, timestamp")
            .order("timestamp", desc=True)
            .limit(200)
            .execute()
        )

        # Deduplicate by city
        seen, city_aqi = set(), {}
        for row in result.data:
            if row["city"] not in seen:
                seen.add(row["city"])
                city_aqi[row["city"]] = row["aqi"]

        # Aggregate by state
        state_buckets: dict[str, list[int]] = {}
        for city, aqi in city_aqi.items():
            state = CITY_STATE_MAP.get(city, "Other")
            state_buckets.setdefault(state, []).append(aqi)

        state_data = []
        for state, values in state_buckets.items():
            avg = round(sum(values) / len(values))
            state_data.append({
                "state":     state,
                "avg_aqi":   avg,
                "city_count": len(values),
                "cities":    [c for c in city_aqi if CITY_STATE_MAP.get(c) == state],
            })

        state_data.sort(key=lambda x: x["avg_aqi"], reverse=True)
        return jsonify(state_data)
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "Internal server error"}), 500
