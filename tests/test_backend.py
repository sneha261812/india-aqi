"""
tests/test_backend.py
Phase 6 — comprehensive backend tests.
Run from backend/: pytest ../tests/test_backend.py -v
"""

import pytest
import json
from unittest.mock import patch, MagicMock


# ── App fixture ─────────────────────────────────────────────────────────────
@pytest.fixture
def app():
    """Create Flask test app with scheduler disabled."""
    with patch("scheduler.init_scheduler"):
        from app import create_app
        application = create_app()
        application.config["TESTING"] = True
        yield application


@pytest.fixture
def client(app):
    return app.test_client()


# ── /ping ────────────────────────────────────────────────────────────────────
class TestPing:
    def test_ping_returns_ok(self, client):
        r = client.get("/ping")
        assert r.status_code == 200
        assert r.json["status"] == "ok"


# ── AQI routes ───────────────────────────────────────────────────────────────
class TestAQIRoutes:
    MOCK_READING = {
        "id": 1, "city": "Delhi", "aqi": 185,
        "pm25": 80.0, "pm10": 120.0, "timestamp": "2024-11-01T12:00:00+00:00",
        "lat": 28.6139, "lon": 77.2090, "source": "waqi",
    }

    def _mock_sb(self, data):
        mock = MagicMock()
        mock.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = data
        return mock

    @patch("routes.aqi_routes.get_supabase")
    def test_current_city_found(self, mock_get_sb, client):
        mock_get_sb.return_value = self._mock_sb([self.MOCK_READING])
        r = client.get("/api/aqi/current/Delhi")
        assert r.status_code == 200
        assert r.json["aqi"] == 185

    @patch("routes.aqi_routes.get_supabase")
    def test_current_city_not_found(self, mock_get_sb, client):
        mock_get_sb.return_value = self._mock_sb([])
        r = client.get("/api/aqi/current/UnknownCity")
        assert r.status_code == 404

    @patch("routes.aqi_routes.get_supabase")
    def test_all_cities(self, mock_get_sb, client):
        rows = [
            {**self.MOCK_READING, "city": "Delhi"},
            {**self.MOCK_READING, "city": "Mumbai", "aqi": 95},
        ]
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.order.return_value \
            .limit.return_value.execute.return_value.data = rows
        mock_get_sb.return_value = mock_sb
        r = client.get("/api/aqi/all")
        assert r.status_code == 200
        assert len(r.json) == 2

    @patch("routes.aqi_routes.get_supabase")
    def test_alerts_endpoint(self, mock_get_sb, client):
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        mock_get_sb.return_value = mock_sb
        r = client.get("/api/aqi/alerts")
        assert r.status_code == 200
        assert isinstance(r.json, list)


# ── Health risk routes ────────────────────────────────────────────────────────
class TestHealthRoutes:
    def test_risk_missing_aqi(self, client):
        r = client.post("/api/health/risk",
                        data=json.dumps({}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_risk_good_aqi(self, client):
        r = client.post("/api/health/risk",
                        data=json.dumps({"aqi": 40}),
                        content_type="application/json")
        assert r.status_code == 200
        assert r.json["category"] == "Good"
        assert r.json["outdoor_safe"] is True

    def test_risk_severe_aqi(self, client):
        r = client.post("/api/health/risk",
                        data=json.dumps({"aqi": 450}),
                        content_type="application/json")
        assert r.status_code == 200
        assert r.json["category"] == "Severe"
        assert r.json["outdoor_safe"] is False
        assert r.json["mask_needed"] is True

    def test_risk_with_profile(self, client):
        r = client.post("/api/health/risk",
                        data=json.dumps({
                            "aqi": 180, "age": 70,
                            "has_asthma": True, "has_heart": False,
                            "pregnant": False, "activity": "exercise",
                        }),
                        content_type="application/json")
        assert r.status_code == 200
        assert len(r.json["sensitive_advice"]) > 0

    def test_risk_invalid_aqi(self, client):
        r = client.post("/api/health/risk",
                        data=json.dumps({"aqi": "bad"}),
                        content_type="application/json")
        assert r.status_code == 400


# ── Chatbot routes ────────────────────────────────────────────────────────────
class TestChatbotRoutes:
    def test_empty_message(self, client):
        r = client.post("/api/chat/message",
                        data=json.dumps({"message": ""}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_message_too_long(self, client):
        r = client.post("/api/chat/message",
                        data=json.dumps({"message": "x" * 1001}),
                        content_type="application/json")
        assert r.status_code == 400

    @patch("routes.chatbot_routes.chat")
    def test_valid_message(self, mock_chat, client):
        mock_chat.return_value = "Delhi AQI is currently 185 — Moderate."
        r = client.post("/api/chat/message",
                        data=json.dumps({"message": "What is the AQI in Delhi?"}),
                        content_type="application/json")
        assert r.status_code == 200
        assert "response" in r.json


# ── Device recommendation routes ──────────────────────────────────────────────
class TestDeviceRoutes:
    def test_missing_room_sqft(self, client):
        r = client.post("/api/devices/recommend",
                        data=json.dumps({"aqi": 200}),
                        content_type="application/json")
        assert r.status_code == 400

    def test_valid_recommendation(self, client):
        r = client.post("/api/devices/recommend",
                        data=json.dumps({"room_sqft": 250, "aqi": 200}),
                        content_type="application/json")
        assert r.status_code == 200
        assert "devices" in r.json
        assert isinstance(r.json["devices"], list)

    def test_budget_filter(self, client):
        r = client.post("/api/devices/recommend",
                        data=json.dumps({"room_sqft": 300, "aqi": 150, "budget_inr": 10000}),
                        content_type="application/json")
        assert r.status_code == 200
        for d in r.json["devices"]:
            assert d["price_inr"] <= 10000


# ── Risk analyzer unit tests ──────────────────────────────────────────────────
class TestRiskAnalyzer:
    def test_good_aqi(self):
        from services.risk_analyzer import analyse
        p = analyse(aqi=30)
        assert p.category == "Good"
        assert p.outdoor_safe is True
        assert p.mask_needed is False

    def test_severe_aqi(self):
        from services.risk_analyzer import analyse
        p = analyse(aqi=450)
        assert p.category == "Severe"
        assert p.risk_level == "Critical"
        assert p.outdoor_safe is False

    def test_sensitive_group_elevated_risk(self):
        from services.risk_analyzer import analyse
        normal   = analyse(aqi=150)
        asthmatic = analyse(aqi=150, has_asthma=True)
        # Sensitive group should have higher or equal risk
        risk_order = ["Low", "Low-Moderate", "Moderate", "High", "Very High", "Critical"]
        assert risk_order.index(asthmatic.risk_level) >= risk_order.index(normal.risk_level)

    def test_child_gets_sensitive_advice(self):
        from services.risk_analyzer import analyse
        p = analyse(aqi=180, age=8)
        assert any("child" in a.lower() or "school" in a.lower() for a in p.sensitive_advice)


# ── Pipeline unit tests ───────────────────────────────────────────────────────
class TestPipeline:
    def test_pm25_to_aqi_good(self):
        from services.pipeline import _pm25_to_aqi
        aqi = _pm25_to_aqi(5.0)
        assert 0 <= aqi <= 50

    def test_pm25_to_aqi_unhealthy(self):
        from services.pipeline import _pm25_to_aqi
        aqi = _pm25_to_aqi(100.0)
        assert 151 <= aqi <= 200

    @patch("services.pipeline.requests.get")
    def test_waqi_invalid_aqi_ignored(self, mock_get):
        mock_get.return_value.json.return_value = {
            "status": "ok",
            "data": {"aqi": -999, "city": {"name": "Test", "geo": [0, 0]}, "iaqi": {}}
        }
        mock_get.return_value.raise_for_status = MagicMock()
        from services.pipeline import fetch_waqi
        result = fetch_waqi("TestCity")
        assert result is None

    @patch("services.pipeline.requests.get")
    def test_waqi_ok_response(self, mock_get):
        mock_get.return_value.json.return_value = {
            "status": "ok",
            "data": {
                "aqi": 150,
                "city": {"name": "Delhi Station", "geo": [28.6, 77.2]},
                "iaqi": {"pm25": {"v": 65}, "pm10": {"v": 90}},
            }
        }
        mock_get.return_value.raise_for_status = MagicMock()
        from services.pipeline import fetch_waqi
        result = fetch_waqi("Delhi")
        assert result is not None
        assert result["aqi"] == 150
        assert result["pm25"] == 65


# ── Device recommender unit tests ─────────────────────────────────────────────
class TestDevices:
    def test_returns_list(self):
        from services.devices import recommend
        result = recommend(room_sqft=250, aqi=200)
        assert isinstance(result, list)

    def test_budget_respected(self):
        from services.devices import recommend
        result = recommend(room_sqft=300, aqi=150, budget_inr=10000)
        for d in result:
            assert d["price_inr"] <= 10000

    def test_smart_only_filter(self):
        from services.devices import recommend
        result = recommend(room_sqft=300, aqi=150, smart_only=True)
        for d in result:
            assert d["smart"] is True

    def test_high_aqi_recommends_higher_cadr(self):
        from services.devices import recommend, _sqft_to_cadr
        low_aqi_cadr  = _sqft_to_cadr(300, 50)
        high_aqi_cadr = _sqft_to_cadr(300, 250)
        assert high_aqi_cadr > low_aqi_cadr
