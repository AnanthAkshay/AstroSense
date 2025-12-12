"""
API Client Manager for NASA DONKI and NOAA SWPC
Handles data retrieval with retry logic, caching, and rate limiting
"""
import httpx
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import wraps
import os
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheEntry:
    """Cache entry with TTL"""
    def __init__(self, data: Any, ttl_seconds: int = 60):
        self.data = data
        self.expires_at = time.time() + ttl_seconds
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class APIClientManager:
    """
    Manages connections to NASA DONKI and NOAA SWPC APIs
    with retry logic, caching, and rate limiting
    """
    
    def __init__(self):
        self.nasa_api_key = os.getenv("NASA_DONKI_API_KEY", "DEMO_KEY")
        self.nasa_base_url = os.getenv("NASA_DONKI_BASE_URL", "https://api.nasa.gov/DONKI")
        self.noaa_base_url = os.getenv("NOAA_SWPC_BASE_URL", "https://services.swpc.noaa.gov/json")
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "60"))
        self.max_retries = 3
        self.cache: Dict[str, CacheEntry] = {}
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0.0
        
    async def _wait_for_rate_limit(self):
        """Ensure rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from URL and parameters"""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{url}?{param_str}"
        return url
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Retrieve data from cache if not expired"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                logger.info(f"Cache hit for {cache_key}")
                return entry.data
            else:
                # Remove expired entry
                del self.cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, data: Any):
        """Add data to cache with TTL"""
        self.cache[cache_key] = CacheEntry(data, self.cache_ttl)
        logger.info(f"Cached data for {cache_key} (TTL: {self.cache_ttl}s)")
    
    async def _make_request_with_retry(
        self, 
        url: str, 
        params: Optional[Dict] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic
        
        Args:
            url: The URL to request
            params: Query parameters
            max_retries: Maximum number of retry attempts (default: self.max_retries)
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: If all retries fail
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Check cache first
        cache_key = self._get_cache_key(url, params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        last_exception = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"Requesting {url} (attempt {attempt + 1}/{max_retries})")
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Cache successful response
                    self._add_to_cache(cache_key, data)
                    
                    return data
                    
            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        logger.error(f"All {max_retries} attempts failed for {url}")
        raise last_exception
    
    async def fetch_donki_cme_events(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch CME events from NASA DONKI API
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            
        Returns:
            Dictionary containing CME events data
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{self.nasa_base_url}/CME"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "api_key": self.nasa_api_key
        }
        
        try:
            data = await self._make_request_with_retry(url, params)
            logger.info(f"Successfully fetched {len(data) if isinstance(data, list) else 1} CME events")
            return {"events": data, "source": "NASA_DONKI", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Failed to fetch CME events: {str(e)}")
            raise
    
    async def fetch_donki_solar_flares(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch solar flare events from NASA DONKI API
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            
        Returns:
            Dictionary containing solar flare data
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{self.nasa_base_url}/FLR"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "api_key": self.nasa_api_key
        }
        
        try:
            data = await self._make_request_with_retry(url, params)
            logger.info(f"Successfully fetched {len(data) if isinstance(data, list) else 1} solar flare events")
            return {"events": data, "source": "NASA_DONKI", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Failed to fetch solar flare events: {str(e)}")
            raise
    
    async def fetch_noaa_solar_wind(self) -> Dict[str, Any]:
        """
        Fetch current solar wind data from NOAA SWPC
        
        Returns:
            Dictionary containing solar wind speed, Bz field, density, etc.
        """
        url = f"{self.noaa_base_url}/plasma-7-day.json"
        
        try:
            data = await self._make_request_with_retry(url)
            
            # NOAA returns array of measurements, get the most recent
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                # Parse NOAA format: [time_tag, density, speed, temperature]
                result = {
                    "timestamp": latest[0] if len(latest) > 0 else None,
                    "density": latest[1] if len(latest) > 1 else None,
                    "speed": latest[2] if len(latest) > 2 else None,
                    "temperature": latest[3] if len(latest) > 3 else None,
                    "source": "NOAA_SWPC"
                }
                
                logger.info(f"Successfully fetched solar wind data: speed={result['speed']} km/s")
                return result
            else:
                logger.warning("No solar wind data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch solar wind data: {str(e)}")
            raise
    
    async def fetch_noaa_mag_field(self) -> Dict[str, Any]:
        """
        Fetch magnetic field data (Bz component) from NOAA SWPC
        
        Returns:
            Dictionary containing Bz magnetic field measurements
        """
        url = f"{self.noaa_base_url}/mag-7-day.json"
        
        try:
            data = await self._make_request_with_retry(url)
            
            # NOAA returns array of measurements, get the most recent
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                # Parse NOAA format: [time_tag, bx, by, bz, lon, lat, bt]
                result = {
                    "timestamp": latest[0] if len(latest) > 0 else None,
                    "bx": latest[1] if len(latest) > 1 else None,
                    "by": latest[2] if len(latest) > 2 else None,
                    "bz": latest[3] if len(latest) > 3 else None,
                    "bt": latest[6] if len(latest) > 6 else None,
                    "source": "NOAA_SWPC"
                }
                
                logger.info(f"Successfully fetched magnetic field data: Bz={result['bz']} nT")
                return result
            else:
                logger.warning("No magnetic field data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch magnetic field data: {str(e)}")
            raise
    
    async def fetch_noaa_kp_index(self) -> Dict[str, Any]:
        """
        Fetch Kp-index data from NOAA SWPC
        
        Returns:
            Dictionary containing Kp-index measurements
        """
        url = f"{self.noaa_base_url}/planetary_k_index_1m.json"
        
        try:
            data = await self._make_request_with_retry(url)
            
            # Get most recent Kp index
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                result = {
                    "timestamp": latest[0] if len(latest) > 0 else None,
                    "kp_index": latest[1] if len(latest) > 1 else None,
                    "source": "NOAA_SWPC"
                }
                
                logger.info(f"Successfully fetched Kp-index: {result['kp_index']}")
                return result
            else:
                logger.warning("No Kp-index data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch Kp-index: {str(e)}")
            raise
    
    async def fetch_all_space_weather_data(self) -> Dict[str, Any]:
        """
        Fetch all space weather data from both NASA and NOAA sources
        
        Returns:
            Dictionary containing all space weather measurements
        """
        logger.info("Fetching all space weather data...")
        
        try:
            # Fetch all data concurrently
            results = await asyncio.gather(
                self.fetch_noaa_solar_wind(),
                self.fetch_noaa_mag_field(),
                self.fetch_noaa_kp_index(),
                self.fetch_donki_cme_events(),
                self.fetch_donki_solar_flares(),
                return_exceptions=True
            )
            
            solar_wind, mag_field, kp_index, cme_events, solar_flares = results
            
            # Combine all data
            combined_data = {
                "timestamp": datetime.now().isoformat(),
                "solar_wind": solar_wind if not isinstance(solar_wind, Exception) else {"error": str(solar_wind)},
                "magnetic_field": mag_field if not isinstance(mag_field, Exception) else {"error": str(mag_field)},
                "kp_index": kp_index if not isinstance(kp_index, Exception) else {"error": str(kp_index)},
                "cme_events": cme_events if not isinstance(cme_events, Exception) else {"error": str(cme_events)},
                "solar_flares": solar_flares if not isinstance(solar_flares, Exception) else {"error": str(solar_flares)}
            }
            
            logger.info("Successfully fetched all space weather data")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching space weather data: {str(e)}")
            raise


# Global instance
api_client = APIClientManager()
