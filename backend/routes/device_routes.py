"""
routes/device_routes.py
Air purifier recommendation endpoints.
"""

from flask import Blueprint, jsonify, request
from services.devices import recommend
import logging

logger = logging.getLogger(__name__)
device_bp = Blueprint("devices", __name__)


@device_bp.route("/recommend", methods=["POST"])
def get_recommendations():
    """
    Recommend air purifiers.

    Body JSON:
      { "room_sqft": 250, "aqi": 210, "budget_inr": 20000, "smart_only": false }
    """
    body = request.get_json(silent=True) or {}
    room_sqft = body.get("room_sqft")
    aqi       = body.get("aqi", 150)

    if not room_sqft:
        return jsonify({"error": "room_sqft is required"}), 400
    try:
        room_sqft = int(room_sqft)
        aqi       = int(aqi)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid numeric values"}), 400

    devices = recommend(
        room_sqft=room_sqft,
        aqi=aqi,
        budget_inr=body.get("budget_inr"),
        smart_only=bool(body.get("smart_only", False)),
    )
    return jsonify({"devices": devices, "count": len(devices)})
