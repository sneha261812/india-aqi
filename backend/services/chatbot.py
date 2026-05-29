"""
services/chatbot.py — DEFINITIVE FIX
Root cause confirmed from Render logs:
  Key valid (54 models). This key has gemini-2.x models, NOT gemini-1.5.
  Available: gemini-2.5-flash, gemini-2.0-flash, gemini-2.5-pro, etc.
  Fix: detect available models dynamically + use correct names.
"""

import os
import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

MAX_TOKENS     = 800
RATE_LIMIT_SEC = 1.5
_last_call     = 0.0
_working_model = None
_available_models = None   # populated on first call from live API

SYSTEM_PROMPT = """You are AQI Saathi, an expert AI assistant for India's air quality.

Responsibilities:
- Explain AQI values and health impacts for Indian users
- Give personalised advice based on pollution levels
- Explain causes: traffic, crop burning, Diwali, industry
- Recommend N95 masks and air purifiers for Indian homes
- Discuss seasonal patterns: winter smog, post-Diwali spikes

India National AQI scale:
  0-50 Good | 51-100 Satisfactory | 101-200 Moderate
  201-300 Poor | 301-400 Very Poor | 401-500 Severe

Be concise, factual and caring. Use live AQI data when provided."""


def _get_available_models(api_key: str) -> list[str]:
    """Fetch actual models available for this API key and return usable names."""
    global _available_models
    if _available_models is not None:
        return _available_models

    try:
        genai.configure(api_key=api_key)
        all_models = list(genai.list_models())
        
        # Filter to models that support generateContent
        usable = []
        for m in all_models:
            if 'generateContent' in m.supported_generation_methods:
                # Strip "models/" prefix — SDK adds it back
                name = m.name.replace('models/', '')
                usable.append(name)
        
        logger.info(f"[GEMINI] Key valid — {len(all_models)} total, {len(usable)} generateContent models")
        logger.info(f"[GEMINI] Available models: {usable[:8]}")
        
        # Prefer in this order: 2.5-flash first (fastest+best), then 2.0, then others
        priority = [
            'gemini-2.5-flash',
            'gemini-2.0-flash', 
            'gemini-2.0-flash-001',
            'gemini-2.5-pro',
            'gemini-2.0-flash-lite',
            'gemini-2.0-flash-lite-001',
            'gemini-1.5-flash-002',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-002',
        ]
        
        ordered = []
        # Add priority models first if available
        for p in priority:
            if p in usable:
                ordered.append(p)
        # Add any remaining models not in priority list
        for u in usable:
            if u not in ordered:
                ordered.append(u)
        
        logger.info(f"[GEMINI] Will use models in order: {ordered[:4]}")
        _available_models = ordered
        return ordered

    except Exception as exc:
        logger.error(f"[GEMINI] Failed to list models: {exc}")
        # Fallback order based on what we know works for newer keys
        fallback = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-2.0-flash-001',
            'gemini-2.5-pro',
            'gemini-1.5-flash-002',
            'gemini-1.5-flash-latest',
        ]
        _available_models = fallback
        return fallback


def _get_aqi_context() -> str:
    """Fetch live AQI — non-fatal if fails."""
    try:
        from db import get_supabase
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("city, aqi")
            .order("timestamp", desc=True)
            .limit(80)
            .execute()
        )
        seen, lines = set(), []
        for row in result.data:
            city = row["city"]
            if city in seen:
                continue
            seen.add(city)
            lines.append(f"  {city}: AQI {row['aqi']}")
            if len(seen) >= 15:
                break
        if lines:
            logger.info(f"[GEMINI] AQI context: {len(seen)} cities")
            return "Current India AQI:\n" + "\n".join(lines)
        return ""
    except Exception as exc:
        logger.warning(f"[GEMINI] AQI context skipped: {exc}")
        return ""


def _try_model(model_name: str, message: str, history: list) -> str | None:
    """Attempt one model. Returns text or None."""
    logger.info(f"[GEMINI] Trying: {model_name}")
    try:
        m = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "max_output_tokens": MAX_TOKENS,
                "temperature": 0.7,
            },
        )
        session  = m.start_chat(history=history)
        response = session.send_message(message)
        logger.info(f"[GEMINI] SUCCESS model={model_name} len={len(response.text)}")
        return response.text
    except Exception as exc:
        logger.error(f"[GEMINI] FAILED model={model_name}: {exc}")
        return None


def chat(user_message: str, history: list[dict] | None = None) -> str:
    global _last_call, _working_model, _available_models

    # Rate limiting
    elapsed = time.time() - _last_call
    if elapsed < RATE_LIMIT_SEC:
        time.sleep(RATE_LIMIT_SEC - elapsed)

    # Validate API key
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.error("[GEMINI] GEMINI_API_KEY not set")
        return "Chatbot not configured — GEMINI_API_KEY missing in Render → Environment."

    genai.configure(api_key=api_key)

    # Get available models for this key (cached after first call)
    models = _get_available_models(api_key)

    # Build message with AQI context
    aqi_context  = _get_aqi_context()
    full_message = (
        f"[LIVE DATA]\n{aqi_context}\n\n" if aqi_context else ""
    ) + user_message

    # Build history
    gemini_history = []
    for turn in (history or []):
        parts = turn.get("parts", [])
        if parts:
            gemini_history.append({
                "role":  turn.get("role", "user"),
                "parts": [str(parts[0])],
            })

    # Try cached working model first
    ordered = []
    if _working_model and _working_model in models:
        ordered.append(_working_model)
    for m in models:
        if m not in ordered:
            ordered.append(m)

    for model_name in ordered:
        result = _try_model(model_name, full_message, gemini_history)
        if result:
            _working_model = model_name
            _last_call     = time.time()
            return result

    logger.error("[GEMINI] ALL MODELS FAILED")
    return (
        "Unable to get a response right now. "
        "Please try again in a moment."
    )
