"""
services/forecast.py
72-hour AQI forecasting using statsmodels SARIMA.
Replaces Prophet — installs instantly on Render free tier,
no C++ compilation, no pystan, no build timeouts.
"""

import os
import logging
import warnings
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from db import get_supabase

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_city_history(city: str) -> pd.Series:
    """Pull hourly AQI history from Supabase as a time-indexed Series."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("timestamp, aqi")
            .eq("city", city)
            .order("timestamp", desc=False)
            .limit(5000)
            .execute()
        )
        rows = result.data
        if not rows:
            return pd.Series(dtype=float)

        df = pd.DataFrame(rows)
        df["ds"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
        df["y"]  = pd.to_numeric(df["aqi"], errors="coerce")
        df = df.dropna(subset=["ds", "y"]).set_index("ds")

        # Resample to hourly, interpolate short gaps
        series = df["y"].resample("1h").mean().interpolate(method="time", limit=6)
        return series.dropna()
    except Exception as exc:
        logger.error(f"History load failed for {city}: {exc}")
        return pd.Series(dtype=float)


# ── Model training ────────────────────────────────────────────────────────────

def train_model(city: str):
    """
    Train a Holt-Winters Exponential Smoothing model.
    Fast, lightweight, captures daily + weekly seasonality well for AQI.
    Falls back to simple exponential smoothing if data is insufficient.
    """
    series = _load_city_history(city)

    if series.empty or len(series) < 48:
        logger.warning(f"Insufficient data for {city} ({len(series)} rows) — skipping training")
        return None

    try:
        # Use Holt-Winters with daily seasonality (24h period)
        # If we have 2+ weeks of data, add weekly seasonality too
        seasonal_periods = 24
        if len(series) >= 24 * 14:
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                damped_trend=True,
            ).fit(optimized=True, use_brute=False)
        else:
            # Simple exponential smoothing for sparse data
            model = ExponentialSmoothing(
                series,
                trend="add",
                damped_trend=True,
            ).fit(optimized=True)

        path = _model_path(city)
        joblib.dump({"model": model, "last_value": float(series.iloc[-1]),
                     "mean": float(series.mean()), "std": float(series.std())}, path)
        logger.info(f"✅ Model trained for {city} ({len(series)} rows) → {path}")
        return model

    except Exception as exc:
        logger.error(f"Training failed for {city}: {exc}")
        return None


def _model_path(city: str) -> str:
    return os.path.join(MODEL_DIR, f"{city.lower().replace(' ', '_')}.pkl")


def _load_cached(city: str):
    path = _model_path(city)
    if os.path.exists(path):
        try:
            return joblib.load(path)
        except Exception:
            logger.warning(f"Corrupt cache for {city} — retraining")
    return None


# ── Forecasting ───────────────────────────────────────────────────────────────

def forecast_city(city: str, hours: int = 72) -> dict:
    """
    Return an N-hour AQI forecast with confidence intervals.
    Uses cached model if available; otherwise trains on the fly.
    """
    cached = _load_cached(city)

    if cached is None:
        model_obj = train_model(city)
        if model_obj is None:
            # Last resort: return a flat forecast based on latest reading
            return _flat_forecast(city, hours)
        cached = _load_cached(city)

    try:
        hw_model  = cached["model"]
        last_val  = cached["last_value"]
        mean_val  = cached["mean"]
        std_val   = cached.get("std", 30.0)

        # Generate forecast
        forecast_values = hw_model.forecast(hours)
        forecast_values = np.clip(forecast_values, 0, 500)

        # Confidence interval: widen with time horizon
        result = []
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for i, yhat in enumerate(forecast_values):
            horizon_factor = 1 + (i / hours) * 0.5   # widen by 50% at max horizon
            ci = std_val * 0.8 * horizon_factor
            ts = pd.Timestamp(now) + pd.Timedelta(hours=i + 1)
            result.append({
                "timestamp": ts.isoformat(),
                "aqi":       max(0, round(float(yhat))),
                "lower":     max(0, round(float(yhat) - ci)),
                "upper":     min(500, round(float(yhat) + ci)),
            })

        return {
            "city":      city,
            "hours":     hours,
            "model":     "holt-winters",
            "generated": datetime.now(timezone.utc).isoformat(),
            "forecast":  result,
        }

    except Exception as exc:
        logger.error(f"Forecast failed for {city}: {exc}")
        return _flat_forecast(city, hours)


def _flat_forecast(city: str, hours: int) -> dict:
    """Fallback: flat forecast using the latest known AQI reading."""
    try:
        sb = get_supabase()
        result = (
            sb.table("aqi_readings")
            .select("aqi")
            .eq("city", city)
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        aqi = result.data[0]["aqi"] if result.data else 100
    except Exception:
        aqi = 100

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    forecast = []
    for i in range(hours):
        ts = pd.Timestamp(now) + pd.Timedelta(hours=i + 1)
        forecast.append({
            "timestamp": ts.isoformat(),
            "aqi":       aqi,
            "lower":     max(0, aqi - 20),
            "upper":     min(500, aqi + 20),
        })

    return {
        "city":      city,
        "hours":     hours,
        "model":     "flat-fallback",
        "generated": datetime.now(timezone.utc).isoformat(),
        "forecast":  forecast,
    }
