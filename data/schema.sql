-- ============================================================
-- India AQI Intelligence Platform — Supabase Schema
-- Run this in your Supabase SQL editor
-- ============================================================

-- ── AQI readings ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aqi_readings (
    id            BIGSERIAL PRIMARY KEY,
    city          TEXT NOT NULL,
    aqi           INTEGER NOT NULL CHECK (aqi >= 0 AND aqi <= 999),
    station       TEXT,
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    pm25          DOUBLE PRECISION,
    pm10          DOUBLE PRECISION,
    no2           DOUBLE PRECISION,
    so2           DOUBLE PRECISION,
    co            DOUBLE PRECISION,
    o3            DOUBLE PRECISION,
    temperature   DOUBLE PRECISION,
    humidity      DOUBLE PRECISION,
    windspeed     DOUBLE PRECISION,
    winddirection DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    source        TEXT DEFAULT 'waqi',
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_aqi_city_ts
    ON aqi_readings (city, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_aqi_timestamp
    ON aqi_readings (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_aqi_city
    ON aqi_readings (city);

-- ── AQI alerts ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aqi_alerts (
    id          BIGSERIAL PRIMARY KEY,
    city        TEXT NOT NULL,
    aqi         INTEGER NOT NULL,
    alert_type  TEXT NOT NULL,   -- 'spike' | 'surge' | 'hazardous'
    message     TEXT NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved    BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_city
    ON aqi_alerts (city, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_unresolved
    ON aqi_alerts (resolved, timestamp DESC);

-- ── Forecast cache (optional — speeds up repeat requests) ───
CREATE TABLE IF NOT EXISTS forecast_cache (
    id          BIGSERIAL PRIMARY KEY,
    city        TEXT NOT NULL,
    forecast    JSONB NOT NULL,
    generated   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_forecast_city
    ON forecast_cache (city);

-- ── Row Level Security ──────────────────────────────────────
-- Allow public read (needed for React frontend using anon key)
ALTER TABLE aqi_readings   ENABLE ROW LEVEL SECURITY;
ALTER TABLE aqi_alerts     ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecast_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read aqi_readings"   ON aqi_readings   FOR SELECT USING (true);
CREATE POLICY "Public read aqi_alerts"     ON aqi_alerts     FOR SELECT USING (true);
CREATE POLICY "Public read forecast_cache" ON forecast_cache FOR SELECT USING (true);

-- Backend uses service role key (bypasses RLS) for writes — no insert policy needed.

-- ── Verify ──────────────────────────────────────────────────
SELECT 'Schema installed successfully ✅' AS status;
