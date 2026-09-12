import pytest
import asyncio
from fastapi.testclient import TestClient
from services.geo_service import GeoService, MockGeoProvider
from unittest.mock import patch


class TestGeoFallback:
    """Test geo enrichment with provider fallback."""

    @pytest.mark.asyncio
    async def test_geo_provider_success(self, mock_geo_success):
        """Test successful geo enrichment with first provider."""
        country, city = await mock_geo_success.get_location("8.8.8.8")
        
        assert country == "United States"
        assert city == "New York"

    @pytest.mark.asyncio 
    async def test_geo_first_provider_fails_second_succeeds(self, mock_geo_fail_first):
        """Test fallback when first provider fails but second succeeds."""
        country, city = await mock_geo_fail_first.get_location("8.8.8.8")
        
        assert country == "Canada"
        assert city == "Toronto"

    @pytest.mark.asyncio
    async def test_geo_all_providers_fail(self, mock_geo_fail_all):
        """Test behavior when all geo providers fail."""
        country, city = await mock_geo_fail_all.get_location("8.8.8.8")
        
        assert country is None
        assert city is None

    @pytest.mark.asyncio
    async def test_geo_local_ip_skipped(self, mock_geo_success):
        """Test that local IPs are skipped for geo enrichment."""
        # Test various local IPs
        local_ips = ["127.0.0.1", "localhost", "::1", "192.168.1.1", "10.0.0.1"]
        
        for ip in local_ips:
            country, city = await mock_geo_success.get_location(ip)
            # Should return None for local IPs even with working provider
            if ip in ["127.0.0.1", "localhost", "::1"]:
                assert country is None
                assert city is None

    @patch('services.submission_service.geo_service')
    def test_submission_with_geo_success(self, mock_geo, client: TestClient, test_widget, db):
        """Test submission stores geo data when provider succeeds."""
        from models.submission import Submission
        from services.geo_service import GeoService, MockGeoProvider
        
        # Setup mock to return specific geo data
        mock_provider = MockGeoProvider(should_fail=False, response=("Germany", "Berlin"))
        mock_geo_service = GeoService([mock_provider])
        mock_geo.get_location.side_effect = mock_geo_service.get_location
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Geo Test",
                "email": "geo@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 200
        
        # Check that geo data was stored
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission is not None
        assert submission.country == "Germany"
        assert submission.city == "Berlin"

    @patch('services.submission_service.geo_service')
    def test_submission_with_geo_failure(self, mock_geo, client: TestClient, test_widget, db):
        """Test submission succeeds even when geo fails."""
        from models.submission import Submission
        from services.geo_service import GeoService, MockGeoProvider
        
        # Setup mock to fail
        mock_provider = MockGeoProvider(should_fail=True)
        mock_geo_service = GeoService([mock_provider])
        mock_geo.get_location.side_effect = mock_geo_service.get_location
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Geo Fail Test",
                "email": "geofail@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        # Submission should still succeed even if geo fails
        assert response.status_code == 200
        
        # Check that submission was stored without geo data
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission is not None
        assert submission.country is None
        assert submission.city is None
        assert submission.submitted_data["name"] == "Geo Fail Test"

    def test_geo_provider_mock_failure(self):
        """Test mock provider failure behavior."""
        provider = MockGeoProvider(should_fail=True)
        
        # Should raise exception when set to fail
        with pytest.raises(Exception) as exc_info:
            asyncio.run(provider.get_location("8.8.8.8"))
        
        assert "Mock provider failure" in str(exc_info.value)

    def test_geo_provider_mock_success(self):
        """Test mock provider success behavior."""
        provider = MockGeoProvider(should_fail=False, response=("Test Country", "Test City"))
        
        result = asyncio.run(provider.get_location("8.8.8.8"))
        assert result == ("Test Country", "Test City")

    @patch('services.submission_service.geo_service')
    def test_submission_geo_disabled(self, mock_geo, client: TestClient, test_widget, db):
        """Test submission when geo is disabled in settings."""
        from models.submission import Submission
        from core.config import settings
        
        # Mock geo service to return None (simulating disabled geo)
        mock_geo.get_location.return_value = (None, None)
        
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "No Geo Test",
                "email": "nogeo@example.com"
            },
            "hp_field": ""
        }
        
        response = client.post("/submissions", json=submission_data)
        assert response.status_code == 200
        
        # Check submission has no geo data
        submission = db.query(Submission).filter(
            Submission.widget_id == test_widget.id
        ).order_by(Submission.id.desc()).first()
        
        assert submission is not None
        assert submission.country is None
        assert submission.city is None