"""
routes/chatbot_routes.py
Gemini AQI chatbot endpoints.
"""

from flask import Blueprint, jsonify, request
from services.chatbot import chat
import logging

logger = logging.getLogger(__name__)
chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/message", methods=["POST"])
def message():
    """
    Send a message to the AQI chatbot.

    Body JSON:
      {
        "message": "What is the AQI in Delhi today?",
        "history": [
          {"role": "user",  "parts": ["Hello"]},
          {"role": "model", "parts": ["Hi! How can I help?"]}
        ]
      }
    """
    body = request.get_json(silent=True) or {}
    user_msg = body.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Message cannot be empty"}), 400
    if len(user_msg) > 1000:
        return jsonify({"error": "Message too long (max 1000 chars)"}), 400

    history = body.get("history", [])
    if not isinstance(history, list):
        history = []

    try:
        response = chat(user_msg, history)
        return jsonify({"response": response})
    except Exception as exc:
        logger.error(f"Chatbot error: {exc}")
        return jsonify({"error": "Chatbot unavailable — please try again"}), 503
