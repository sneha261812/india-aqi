"""
routes/forecast_routes.py
Prophet forecast endpoints.
"""

from flask import Blueprint, jsonify, request
from services.forecast import forecast_city, train_model
import logging

logger = logging.getLogger(__name__)
forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/<city>", methods=["GET"])
def get_forecast(city):
    """
    72-hour AQI forecast for a city.
    Optional: ?hours=N (max 168)
    """
    hours = request.args.get("hours", 72, type=int)
    hours = min(hours, 168)
    result = forecast_city(city, hours)
    if "error" in result:
        return jsonify(result), 422
    return jsonify(result)


@forecast_bp.route("/train/<city>", methods=["POST"])
def trigger_training(city):
    """Manually trigger model re-training for a city."""
    model = train_model(city)
    if model is None:
        return jsonify({"error": f"Training failed for {city} — insufficient data"}), 422
    return jsonify({"status": "ok", "message": f"Model trained for {city}"})
