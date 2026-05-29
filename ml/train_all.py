"""
ml/train_all.py
Bulk-train Holt-Winters models for all monitored cities.
Run from the backend/ directory:
    cd backend && python ../ml/train_all.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from scheduler import INDIAN_CITIES
from services.forecast import train_model
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


def main():
    success, failed, skipped = [], [], []
    for city in INDIAN_CITIES:
        model = train_model(city)
        if model is None:
            skipped.append(city)   # not enough data yet — will auto-train later
        else:
            success.append(city)

    print(f"\n{'='*50}")
    print(f"✅ Trained:  {len(success)} cities")
    print(f"⏭  Skipped:  {len(skipped)} cities (not enough data yet)")
    if skipped:
        print("  Skipped:", ", ".join(skipped))
    print(f"{'='*50}")
    print("Models auto-retrain as data accumulates via /api/forecast/<city>")


if __name__ == "__main__":
    main()
