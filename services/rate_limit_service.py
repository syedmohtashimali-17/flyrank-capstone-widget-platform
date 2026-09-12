import time
from typing import Dict, Tuple
from core.config import settings
from core.errors import TooManyRequestsError


class RateLimitService:
    """Simple in-memory rate limiter for development.
    
    Note: In production, this should use Redis or another shared store
    for multi-instance deployments.
    """
    
    def __init__(self):
        self._ip_requests: Dict[str, list] = {}
        self._widget_requests: Dict[str, list] = {}
        
        # Parse rate limits
        self.ip_limit, self.ip_window = self._parse_rate_limit(settings.rate_limit_per_ip)
        self.widget_limit, self.widget_window = self._parse_rate_limit(settings.rate_limit_per_widget)
    
    def _parse_rate_limit(self, rate_string: str) -> Tuple[int, int]:
        """Parse rate limit string like '10/minute' into (limit, window_seconds)."""
        parts = rate_string.split('/')
        limit = int(parts[0])
        
        window_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        window = window_map.get(parts[1], 60)  # Default to minute
        return limit, window
    
    def _clean_old_requests(self, requests: list, window: int) -> None:
        """Remove requests older than the window."""
        current_time = time.time()
        cutoff_time = current_time - window
        
        # Remove old requests
        while requests and requests[0] < cutoff_time:
            requests.pop(0)
    
    def check_ip_rate_limit(self, ip_address: str) -> None:
        """Check if IP is within rate limits."""
        if ip_address not in self._ip_requests:
            self._ip_requests[ip_address] = []
        
        requests = self._ip_requests[ip_address]
        self._clean_old_requests(requests, self.ip_window)
        
        if len(requests) >= self.ip_limit:
            raise TooManyRequestsError("IP rate limit exceeded")
        
        requests.append(time.time())
    
    def check_widget_rate_limit(self, widget_id: str) -> None:
        """Check if widget is within rate limits."""
        if widget_id not in self._widget_requests:
            self._widget_requests[widget_id] = []
        
        requests = self._widget_requests[widget_id]
        self._clean_old_requests(requests, self.widget_window)
        
        if len(requests) >= self.widget_limit:
            raise TooManyRequestsError("Widget rate limit exceeded")
        
        requests.append(time.time())
    
    def check_rate_limits(self, ip_address: str, widget_id: str) -> None:
        """Check both IP and widget rate limits."""
        self.check_ip_rate_limit(ip_address)
        self.check_widget_rate_limit(widget_id)


# Global instance
rate_limiter = RateLimitService()