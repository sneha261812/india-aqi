"""
services/risk_analyzer.py
Generates personalised health risk profiles from AQI + user attributes.
"""

from __future__ import annotations
from dataclasses import dataclass

# India National AQI breakpoints
AQI_CATEGORIES = [
    (0,   50,  "Good",         "#00b050"),
    (51,  100, "Satisfactory", "#92d050"),
    (101, 200, "Moderate",     "#ffff00"),
    (201, 300, "Poor",         "#ff9900"),
    (301, 400, "Very Poor",    "#ff0000"),
    (401, 500, "Severe",       "#c00000"),
]


@dataclass
class RiskProfile:
    aqi:              int
    category:         str
    color:            str
    risk_level:       str           # Low / Moderate / High / Very High / Critical
    outdoor_safe:     bool
    mask_needed:      bool
    purifier_advised: bool
    advice:           list[str]
    sensitive_advice: list[str]


def _categorise(aqi: int) -> tuple[str, str]:
    for lo, hi, label, color in AQI_CATEGORIES:
        if lo <= aqi <= hi:
            return label, color
    return "Severe", "#c00000"


def analyse(
    aqi: int,
    age: int | None = None,
    has_asthma: bool = False,
    has_heart: bool = False,
    pregnant: bool = False,
    activity: str = "normal",      # "normal" | "exercise" | "indoor"
) -> RiskProfile:
    """
    Return a full RiskProfile for the given AQI and user health attributes.
    activity: intended outdoor activity level
    """
    category, color = _categorise(aqi)

    # Base risk level
    if aqi <= 50:
        risk_level = "Low"
    elif aqi <= 100:
        risk_level = "Low-Moderate"
    elif aqi <= 200:
        risk_level = "Moderate"
    elif aqi <= 300:
        risk_level = "High"
    elif aqi <= 400:
        risk_level = "Very High"
    else:
        risk_level = "Critical"

    # Elevated risk for sensitive groups
    sensitive = has_asthma or has_heart or pregnant or (age is not None and (age < 12 or age > 65))
    if sensitive and aqi > 100:
        risk_level = _elevate(risk_level)

    outdoor_safe     = aqi <= 100
    mask_needed      = aqi > 150 or (aqi > 100 and sensitive)
    purifier_advised = aqi > 100

    # Build advice
    advice = _base_advice(aqi, activity)
    sensitive_advice = _sensitive_advice(aqi, has_asthma, has_heart, pregnant, age)

    return RiskProfile(
        aqi=aqi,
        category=category,
        color=color,
        risk_level=risk_level,
        outdoor_safe=outdoor_safe,
        mask_needed=mask_needed,
        purifier_advised=purifier_advised,
        advice=advice,
        sensitive_advice=sensitive_advice,
    )


def _elevate(level: str) -> str:
    order = ["Low", "Low-Moderate", "Moderate", "High", "Very High", "Critical"]
    idx = order.index(level) if level in order else 0
    return order[min(idx + 1, len(order) - 1)]


def _base_advice(aqi: int, activity: str) -> list[str]:
    if aqi <= 50:
        return ["Air quality is excellent — enjoy outdoor activities freely."]
    if aqi <= 100:
        return [
            "Air quality is acceptable for most people.",
            "Unusually sensitive individuals may experience minor symptoms.",
        ]
    if aqi <= 200:
        base = ["Reduce prolonged outdoor exertion.", "Close windows during peak traffic hours."]
        if activity == "exercise":
            base.append("Consider moving exercise indoors or early morning (5–7 AM).")
        return base
    if aqi <= 300:
        return [
            "Limit outdoor activities — especially strenuous exercise.",
            "Wear an N95 mask if you must go outside.",
            "Keep windows and doors closed.",
            "Run an air purifier indoors if available.",
        ]
    if aqi <= 400:
        return [
            "Avoid all outdoor activities.",
            "Wear N95 mask even indoors if purifier is unavailable.",
            "Seal window gaps with wet cloth if needed.",
            "Stay well hydrated and monitor health closely.",
        ]
    return [
        "🚨 Emergency pollution levels. Stay indoors at all times.",
        "Use N95 mask indoors. Seal all ventilation.",
        "Schools, outdoor events should be cancelled.",
        "Seek medical attention if you experience breathing difficulty.",
    ]


def _sensitive_advice(
    aqi: int, asthma: bool, heart: bool, pregnant: bool, age: int | None
) -> list[str]:
    tips = []
    if asthma and aqi > 100:
        tips.append("Keep your reliever inhaler accessible at all times.")
        tips.append("Pre-medicate before any outdoor exposure as advised by doctor.")
    if heart and aqi > 100:
        tips.append("Avoid physical exertion — pollution stresses the cardiovascular system.")
        tips.append("Monitor blood pressure and report chest tightness to your doctor.")
    if pregnant and aqi > 100:
        tips.append("Minimise outdoor time — fine particles can cross the placental barrier.")
        tips.append("Ensure indoor AQI is monitored and purifier is running.")
    if age is not None and age < 12 and aqi > 100:
        tips.append("Children should not play outdoors today.")
        tips.append("Schools should cancel outdoor sports or recess.")
    if age is not None and age > 65 and aqi > 100:
        tips.append("Elderly individuals face higher risk. Remain indoors and rest.")
    return tips
