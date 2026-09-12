import pytest
import time
from fastapi.testclient import TestClient
from services.rate_limit_service import RateLimitService


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_service_ip_limit(self):
        """Test IP rate limiting logic."""
        rate_limiter = RateLimitService()
        rate_limiter.ip_limit = 3
        rate_limiter.ip_window = 60
        
        # Clear any existing data
        rate_limiter._ip_requests.clear()
        
        # Should allow requests up to the limit
        for i in range(3):
            rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        # Fourth request should raise error
        with pytest.raises(Exception) as exc_info:
            rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        assert "rate limit exceeded" in str(exc_info.value).lower()

    def test_rate_limit_service_widget_limit(self):
        """Test widget rate limiting logic."""
        rate_limiter = RateLimitService()
        rate_limiter.widget_limit = 2
        rate_limiter.widget_window = 60
        
        # Clear any existing data
        rate_limiter._widget_requests.clear()
        
        # Should allow requests up to the limit
        for i in range(2):
            rate_limiter.check_widget_rate_limit("test-widget-123")
        
        # Third request should raise error
        with pytest.raises(Exception) as exc_info:
            rate_limiter.check_widget_rate_limit("test-widget-123")
        
        assert "rate limit exceeded" in str(exc_info.value).lower()

    def test_rate_limit_different_ips(self):
        """Test that different IPs have separate rate limits."""
        rate_limiter = RateLimitService()
        rate_limiter.ip_limit = 2
        rate_limiter.ip_window = 60
        
        # Clear any existing data
        rate_limiter._ip_requests.clear()
        
        # Use up limit for first IP
        rate_limiter.check_ip_rate_limit("192.168.1.100")
        rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        # Third request from same IP should fail
        with pytest.raises(Exception):
            rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        # But different IP should still work
        rate_limiter.check_ip_rate_limit("192.168.1.101")

    def test_rate_limit_window_expiry(self):
        """Test that rate limits reset after window expires."""
        rate_limiter = RateLimitService()
        rate_limiter.ip_limit = 2
        rate_limiter.ip_window = 1  # 1 second window for testing
        
        # Clear any existing data
        rate_limiter._ip_requests.clear()
        
        # Use up the limit
        rate_limiter.check_ip_rate_limit("192.168.1.100")
        rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        # Should fail immediately
        with pytest.raises(Exception):
            rate_limiter.check_ip_rate_limit("192.168.1.100")
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should work again after window expires
        rate_limiter.check_ip_rate_limit("192.168.1.100")

    def test_submission_rate_limiting_integration(self, client: TestClient, test_widget):
        """Test rate limiting in actual submission endpoint."""
        submission_data = {
            "widget_id": test_widget.id,
            "data": {
                "name": "Rate Test",
                "email": "rate@example.com"
            },
            "hp_field": ""
        }
        
        # Make several requests quickly
        responses = []
        for i in range(15):  # More than the default limit
            response = client.post("/submissions", json=submission_data)
            responses.append(response)
        
        # Count status codes
        status_codes = [r.status_code for r in responses]
        
        # Should have some 200s and some 429s (rate limited)
        assert 200 in status_codes
        assert 429 in status_codes
        
        # Find first rate limited response
        rate_limited_response = next(r for r in responses if r.status_code == 429)
        data = rate_limited_response.json()
        assert data["error"]["code"] == "TOO_MANY_REQUESTS"

    def test_rate_limit_parse_config(self):
        """Test rate limit configuration parsing."""
        rate_limiter = RateLimitService()
        
        # Test different time units
        limit, window = rate_limiter._parse_rate_limit("10/minute")
        assert limit == 10
        assert window == 60
        
        limit, window = rate_limiter._parse_rate_limit("5/second")
        assert limit == 5
        assert window == 1
        
        limit, window = rate_limiter._parse_rate_limit("100/hour")
        assert limit == 100
        assert window == 3600

    def test_rate_limit_both_dimensions(self):
        """Test that both IP and widget limits are enforced."""
        rate_limiter = RateLimitService()
        rate_limiter.ip_limit = 5
        rate_limiter.widget_limit = 3
        rate_limiter.ip_window = 60
        rate_limiter.widget_window = 60
        
        # Clear existing data
        rate_limiter._ip_requests.clear()
        rate_limiter._widget_requests.clear()
        
        # Use up widget limit first (3 requests)
        for i in range(3):
            rate_limiter.check_rate_limits("192.168.1.100", "test-widget")
        
        # Fourth request should fail on widget limit even though IP limit not reached
        with pytest.raises(Exception) as exc_info:
            rate_limiter.check_rate_limits("192.168.1.100", "test-widget")
        
        assert "rate limit exceeded" in str(exc_info.value).lower()