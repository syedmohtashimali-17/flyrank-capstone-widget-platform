import asyncio
import logging
from typing import Optional, Tuple, Protocol
import httpx
from core.config import settings

logger = logging.getLogger(__name__)


class GeoProvider(Protocol):
    """Protocol for geo providers."""
    
    async def get_location(self, ip: str) -> Optional[Tuple[str, str]]:
        """Get (country, city) for IP address."""
        pass


class IPApiProvider:
    """ip-api.com provider."""
    
    def __init__(self, base_url: str = "http://ip-api.com/json/"):
        self.base_url = base_url.rstrip('/')
    
    async def get_location(self, ip: str) -> Optional[Tuple[str, str]]:
        """Get location from ip-api.com."""
        try:
            async with httpx.AsyncClient(timeout=settings.geo_timeout) as client:
                response = await client.get(f"{self.base_url}/{ip}")
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') == 'success':
                    country = data.get('country')
                    city = data.get('city')
                    if country and city:
                        return country, city
                
        except Exception as e:
            logger.warning(f"IP-API provider failed for {ip}: {e}")
        
        return None


class IpapiProvider:
    """ipapi.co provider."""
    
    def __init__(self, base_url: str = "https://ipapi.co/"):
        self.base_url = base_url.rstrip('/')
    
    async def get_location(self, ip: str) -> Optional[Tuple[str, str]]:
        """Get location from ipapi.co."""
        try:
            async with httpx.AsyncClient(timeout=settings.geo_timeout) as client:
                response = await client.get(f"{self.base_url}/{ip}/json/")
                response.raise_for_status()
                
                data = response.json()
                country = data.get('country_name')
                city = data.get('city')
                
                if country and city:
                    return country, city
                
        except Exception as e:
            logger.warning(f"IPAPI provider failed for {ip}: {e}")
        
        return None


class MockGeoProvider:
    """Mock provider for testing."""
    
    def __init__(self, should_fail: bool = False, response: Optional[Tuple[str, str]] = None):
        self.should_fail = should_fail
        self.response = response or ("United States", "New York")
    
    async def get_location(self, ip: str) -> Optional[Tuple[str, str]]:
        """Mock geo response."""
        if self.should_fail:
            raise Exception("Mock provider failure")
        return self.response


class GeoService:
    """Geo enrichment service with fallback chain."""
    
    def __init__(self, providers: Optional[list] = None):
        if providers is None:
            # Default provider chain
            self.providers = [
                IPApiProvider(settings.geo_provider_a_url),
                IpapiProvider(settings.geo_provider_b_url)
            ]
        else:
            self.providers = providers
    
    async def get_location(self, ip_address: str) -> Tuple[Optional[str], Optional[str]]:
        """Get location with provider fallback chain.
        
        Returns (country, city) or (None, None) if all providers fail.
        """
        if not settings.geo_enabled:
            return None, None
        
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            # Skip geo for local IPs
            return None, None
        
        for i, provider in enumerate(self.providers):
            try:
                logger.info(f"Trying geo provider {i+1} for IP {ip_address}")
                result = await provider.get_location(ip_address)
                
                if result:
                    country, city = result
                    logger.info(f"Geo provider {i+1} success: {country}, {city}")
                    return country, city
                else:
                    logger.warning(f"Geo provider {i+1} returned no data for {ip_address}")
                    
            except Exception as e:
                logger.warning(f"Geo provider {i+1} failed for {ip_address}: {e}")
                continue
        
        logger.info(f"All geo providers failed for {ip_address}")
        return None, None


# Global geo service instance
geo_service = GeoService()