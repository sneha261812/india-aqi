"""
db.py — Supabase client singleton.
Uses httpx==0.26.0 which accepts proxy=None from gotrue internals.
Simple create_client — no ClientOptions needed.
"""

import os
import logging

logger  = logging.getLogger(__name__)
_client = None


def get_supabase():
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_KEY") or
        os.getenv("SUPABASE_ANON_KEY") or ""
    ).strip()

    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in Render environment"
        )

    from supabase import create_client
    _client = create_client(url, key)
    logger.info(f"Supabase client ready — {url[:40]}...")
    return _client
