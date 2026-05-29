"""
routes/health_routes.py
Health risk analysis endpoints.
"""

from flask import Blueprint, jsonify, request
from services.risk_analyzer import analyse
import logging

logger = logging.getLogger(__name__)
health_bp = Blueprint("health", __name__)


@health_bp.route("/risk", methods=["POST"])
def risk():
    """
    Personalised AQI health risk assessment.

    Body JSON:
      {
        "aqi": 185,
        "age": 45,
        "has_asthma": false,
        "has_heart": true,
        "pregnant": false,
        "activity": "normal"
      }
    """
    body = request.get_json(silent=True) or {}
    aqi = body.get("aqi")
    if aqi is None:
        return jsonify({"error": "aqi is required"}), 400
    try:
        aqi = int(aqi)
    except (TypeError, ValueError):
        return jsonify({"error": "aqi must be a number"}), 400

    profile = analyse(
        aqi=aqi,
        age=body.get("age"),
        has_asthma=bool(body.get("has_asthma", False)),
        has_heart=bool(body.get("has_heart", False)),
        pregnant=bool(body.get("pregnant", False)),
        activity=body.get("activity", "normal"),
    )

    return jsonify({
        "aqi":              profile.aqi,
        "category":         profile.category,
        "color":            profile.color,
        "risk_level":       profile.risk_level,
        "outdoor_safe":     profile.outdoor_safe,
        "mask_needed":      profile.mask_needed,
        "purifier_advised": profile.purifier_advised,
        "advice":           profile.advice,
        "sensitive_advice": profile.sensitive_advice,
    })
