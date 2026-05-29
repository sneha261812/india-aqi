"""
services/devices.py
Air purifier recommendation engine — room size + AQI → best-fit device.
"""

from __future__ import annotations

DEVICES = [
    {
        "id": "xiaomi-4-lite",
        "name": "Xiaomi Smart Air Purifier 4 Lite",
        "cadr_m3h": 360,
        "room_size_sqft": (0, 400),
        "price_inr": 7999,
        "hepa": True, "activated_carbon": True, "smart": True,
        "best_for": ["small rooms", "bedroom", "budget"],
        "buy_url": "https://www.mi.com/in/product/air-purifier-4-lite",
    },
    {
        "id": "honeywell-air-touch-v2",
        "name": "Honeywell Air Touch V2",
        "cadr_m3h": 250,
        "room_size_sqft": (0, 350),
        "price_inr": 9999,
        "hepa": True, "activated_carbon": True, "smart": False,
        "best_for": ["budget", "small apartment", "bedroom"],
        "buy_url": "https://www.honeywellstore.com",
    },
    {
        "id": "xiaomi-4-pro",
        "name": "Xiaomi Smart Air Purifier 4 Pro",
        "cadr_m3h": 500,
        "room_size_sqft": (150, 650),
        "price_inr": 14999,
        "hepa": True, "activated_carbon": True, "smart": True,
        "best_for": ["living room", "mid-size rooms"],
        "buy_url": "https://www.mi.com/in/product/air-purifier-4-pro",
    },
    {
        "id": "philips-ac2887",
        "name": "Philips Air Purifier AC2887",
        "cadr_m3h": 333,
        "room_size_sqft": (150, 550),
        "price_inr": 18999,
        "hepa": True, "activated_carbon": True, "smart": False,
        "best_for": ["mid-range", "reliable", "living room"],
        "buy_url": "https://www.philips.co.in",
    },
    {
        "id": "sharp-fp-j60m",
        "name": "Sharp Plasmacluster FP-J60M",
        "cadr_m3h": 400,
        "room_size_sqft": (200, 750),
        "price_inr": 27500,
        "hepa": True, "activated_carbon": True, "smart": True,
        "best_for": ["large room", "virus protection", "plasmacluster"],
        "buy_url": "https://www.sharpindia.com/air-purifiers",
    },
    {
        "id": "dyson-tp07",
        "name": "Dyson Purifier Cool TP07",
        "cadr_m3h": 290,
        "room_size_sqft": (100, 500),
        "price_inr": 49900,
        "hepa": True, "activated_carbon": True, "smart": True,
        "best_for": ["premium", "fan + purifier", "bedroom"],
        "buy_url": "https://www.dyson.in",
    },
    {
        "id": "blueair-classic-480i",
        "name": "Blueair Classic 480i",
        "cadr_m3h": 500,
        "room_size_sqft": (300, 900),
        "price_inr": 59000,
        "hepa": True, "activated_carbon": True, "smart": True,
        "best_for": ["large rooms", "premium", "wifi"],
        "buy_url": "https://www.blueair.com/in",
    },
    {
        "id": "iqair-healthpro-plus",
        "name": "IQAir HealthPro Plus",
        "cadr_m3h": 900,
        "room_size_sqft": (400, 1200),
        "price_inr": 135000,
        "hepa": True, "activated_carbon": True, "smart": False,
        "best_for": ["very large rooms", "medical grade", "severe pollution"],
        "buy_url": "https://www.iqair.com/in-en",
    },
]


def _sqft_to_cadr(sqft: int, aqi: int) -> float:
    """Minimum CADR needed: higher AQI → more air changes per hour."""
    volume_m3 = sqft * 0.0929 * 2.7
    ach = 6 if aqi > 300 else 5 if aqi > 200 else 4
    return volume_m3 * ach


def recommend(
    room_sqft: int,
    aqi: int,
    budget_inr: int | None = None,
    smart_only: bool = False,
) -> list[dict]:
    """Return up to 3 best-fit devices sorted by suitability score."""
    min_cadr = _sqft_to_cadr(room_sqft, aqi)

    # Relax room-size constraint by 20% to avoid empty results
    relaxed_sqft = room_sqft * 0.8

    candidates = []
    for d in DEVICES:
        lo, hi = d["room_size_sqft"]
        if not (lo <= relaxed_sqft <= hi):
            continue
        if d["cadr_m3h"] < min_cadr * 0.85:   # allow 15% under-CADR
            continue
        if budget_inr and d["price_inr"] > budget_inr:
            continue
        if smart_only and not d["smart"]:
            continue
        cadr_excess = d["cadr_m3h"] - min_cadr
        price_norm  = d["price_inr"] / 10000
        score       = cadr_excess * 0.3 - price_norm
        candidates.append({**d, "_score": score})

    # If still empty, remove CADR constraint (show best available)
    if not candidates:
        for d in DEVICES:
            lo, hi = d["room_size_sqft"]
            if budget_inr and d["price_inr"] > budget_inr:
                continue
            if smart_only and not d["smart"]:
                continue
            candidates.append({**d, "_score": -d["price_inr"]})

    candidates.sort(key=lambda x: x["_score"], reverse=True)
    result = []
    for c in candidates[:3]:
        c.pop("_score", None)
        result.append(c)
    return result
