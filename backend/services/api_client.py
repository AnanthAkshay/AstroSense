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
        
        # Test mode configuration
        self.max_retries = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.base_backoff = float(os.getenv("BASE_BACKOFF_SECONDS", "1.0"))
        
        self.cache: Dict[str, CacheEntry] = {}
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0.0
        
        # RTSW endpoint candidates (in order of preference)
        self.rtsw_wind_candidates = [
            "rtsw_wind_1m.json",
            "rtsw_plasma_1m.json",  # Legacy name, might still work
        ]
        self.rtsw_mag_candidates = [
            "rtsw_mag_1m.json",
        ]
    
    async def _find_working_rtsw_endpoint(self, candidates: list) -> Optional[str]:
        """
        Find the first working RTSW endpoint from a list of candidates
        
        Args:
            candidates: List of filename candidates to try
            
        Returns:
            Full URL of working endpoint, or None if none work
        """
        rtsw_base = "https://services.swpc.noaa.gov/json/rtsw/"
        
        for filename in candidates:
            url = rtsw_base + filename
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Use HEAD request to check if endpoint exists
                    response = await client.head(url)
                    if response.status_code == 200:
                        logger.info(f"Found working RTSW endpoint: {url}")
                        return url
            except Exception as e:
                logger.debug(f"RTSW endpoint {url} not available: {str(e)}")
                continue
        
        logger.warning(f"No working RTSW endpoints found from candidates: {candidates}")
        return None
        
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
        Make HTTP request with exponential backoff retry logic with jitter
        
        Args:
            url: The URL to request
            params: Query parameters
            max_retries: Maximum number of retry attempts (default: self.max_retries)
            
        Returns:
            JSON response data
            
        Raises:
            httpx.HTTPError: If all retries fail
        """
        import random
        
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
        backoff = self.base_backoff
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"Requesting {url} (attempt {attempt + 1}/{max_retries})")
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Cache successful response
                        self._add_to_cache(cache_key, data)
                        return data
                    
                    elif response.status_code == 404:
                        # Don't retry 404s - resource doesn't exist
                        logger.error(f"Resource not found (404): {url}")
                        response.raise_for_status()
                    
                    elif response.status_code == 429:
                        # Rate limited - respect Retry-After header if present
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            wait_time = float(retry_after)
                            logger.warning(f"Rate limited (429). Waiting {wait_time}s as requested")
                        else:
                            # Use exponential backoff with jitter
                            wait_time = backoff * (1 + random.random() * 0.5)
                            logger.warning(f"Rate limited (429). Waiting {wait_time:.1f}s")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(wait_time)
                            backoff *= 2
                            continue
                        else:
                            response.raise_for_status()
                    
                    else:
                        # Other HTTP errors
                        response.raise_for_status()
                    
            except httpx.HTTPError as e:
                last_exception = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter for network errors
                    wait_time = backoff * (1 + random.random() * 0.3)
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    await asyncio.sleep(wait_time)
                    backoff *= 2
        
        # All retries failed
        logger.error(f"All {max_retries} attempts failed for {url}")
        if last_exception:
            raise last_exception
        else:
            raise httpx.HTTPError(f"All {max_retries} attempts failed for {url}")
    
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
        # Find working RTSW wind endpoint
        url = await self._find_working_rtsw_endpoint(self.rtsw_wind_candidates)
        if not url:
            raise Exception("No working RTSW wind endpoints available")
        
        try:
            data = await self._make_request_with_retry(url)
            
            # NOAA RTSW returns array of JSON objects, get the most recent
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                # Parse NOAA RTSW JSON object format
                result = {
                    "timestamp": latest.get("time_tag"),
                    "density": latest.get("proton_density"),
                    "speed": latest.get("proton_speed"),
                    "temperature": latest.get("proton_temperature"),
                    "source": "NOAA_SWPC_RTSW"
                }
                
                logger.info(f"Successfully fetched solar wind data: speed={result['speed']} km/s")
                return result
            else:
                logger.warning("No solar wind data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch solar wind data: {str(e)}")
            # Fallback: try lower-frequency 1-day plasma data
            try:
                logger.info("Trying fallback 1-day plasma data")
                url_fallback = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
                fallback_data = await self._make_request_with_retry(url_fallback)
                
                if isinstance(fallback_data, list) and len(fallback_data) > 0:
                    latest = fallback_data[-1]
                    result = {
                        "timestamp": latest[0] if len(latest) > 0 else None,
                        "speed": None,  # Not available in magnetometer data
                        "density": None,  # Not available in magnetometer data
                        "temperature": None,  # Not available in magnetometer data
                        "source": "NOAA_SWPC_GOES_FALLBACK",
                        "note": "Limited data from GOES magnetometer"
                    }
                    logger.info("Successfully fetched fallback solar wind data from GOES")
                    return result
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            raise
    
    async def fetch_noaa_mag_field(self) -> Dict[str, Any]:
        """
        Fetch magnetic field data (Bz component) from NOAA SWPC
        
        Returns:
            Dictionary containing Bz magnetic field measurements
        """
        # Find working RTSW magnetometer endpoint
        url = await self._find_working_rtsw_endpoint(self.rtsw_mag_candidates)
        if not url:
            raise Exception("No working RTSW magnetometer endpoints available")
        
        try:
            data = await self._make_request_with_retry(url)
            
            # NOAA returns array of JSON objects, get the most recent
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                # Parse NOAA RTSW JSON object format
                result = {
                    "timestamp": latest.get("time_tag"),
                    "bx_gse": latest.get("bx_gse"),
                    "by_gse": latest.get("by_gse"),
                    "bz_gse": latest.get("bz_gse"),  # GSE coordinates
                    "bx_gsm": latest.get("bx_gsm"),
                    "by_gsm": latest.get("by_gsm"),
                    "bz_gsm": latest.get("bz_gsm"),  # GSM coordinates (more relevant for space weather)
                    "bt": latest.get("bt"),  # Total field magnitude
                    "source": latest.get("source", "NOAA_SWPC"),
                    "active": latest.get("active"),
                    "quality": latest.get("overall_quality")
                }
                
                # Use GSM Bz as primary Bz value (more relevant for geomagnetic effects)
                bz_value = result["bz_gsm"] or result["bz_gse"]
                logger.info(f"Successfully fetched magnetic field data: Bz={bz_value} nT (GSM)")
                return result
            else:
                logger.warning("No magnetic field data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch magnetic field data: {str(e)}")
            # Fallback: try lower-frequency 1-day magnetometer data
            try:
                logger.info("Trying fallback 1-day magnetometer data")
                url_fallback = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
                fallback_data = await self._make_request_with_retry(url_fallback)
                
                if isinstance(fallback_data, list) and len(fallback_data) > 0:
                    latest = fallback_data[-1]
                    
                    # Parse fallback data format
                    result = {
                        "timestamp": latest.get("time_tag"),
                        "bx_gse": latest.get("bx_gse"),
                        "by_gse": latest.get("by_gse"),
                        "bz_gse": latest.get("bz_gse"),
                        "bx_gsm": latest.get("bx_gsm"),
                        "by_gsm": latest.get("by_gsm"),
                        "bz_gsm": latest.get("bz_gsm"),
                        "bt": latest.get("bt"),
                        "source": "NOAA_SWPC_1DAY_FALLBACK"
                    }
                    
                    bz_value = result["bz_gsm"] or result["bz_gse"]
                    logger.info(f"Successfully fetched fallback magnetic field data: Bz={bz_value} nT")
                    return result
                    
            except Exception as fallback_error:
                logger.error(f"Fallback magnetometer data also failed: {str(fallback_error)}")
            
            raise
    
    async def fetch_noaa_kp_index(self) -> Dict[str, Any]:
        """
        Fetch Kp-index data from NOAA SWPC
        
        Returns:
            Dictionary containing Kp-index measurements
        """
        # Try the real-time Kp index first
        url = "https://services.swpc.noaa.gov/json/geomag/rt-kp.json"
        
        try:
            data = await self._make_request_with_retry(url)
            
            # Get most recent Kp index
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                
                result = {
                    "timestamp": latest.get("time_tag"),
                    "kp_index": latest.get("kp_index"),
                    "estimated_kp": latest.get("estimated_kp"),
                    "kp": latest.get("kp"),  # String representation with confidence
                    "source": "NOAA_SWPC"
                }
                
                logger.info(f"Successfully fetched Kp-index: {result['kp_index']} ({result['kp']})")
                return result
            else:
                logger.warning("No Kp-index data available from NOAA")
                return {"error": "No data available", "source": "NOAA_SWPC"}
                
        except Exception as e:
            logger.error(f"Failed to fetch Kp-index: {str(e)}")
            # Fallback: try the planetary K index 1-minute data
            try:
                logger.info("Trying fallback planetary K index data")
                url_fallback = "https://services.swpc.noaa.gov/products/geomag/planetary_k_index_1m.json"
                fallback_data = await self._make_request_with_retry(url_fallback)
                
                if isinstance(fallback_data, list) and len(fallback_data) > 0:
                    latest = fallback_data[-1]
                    
                    result = {
                        "timestamp": latest.get("time_tag"),
                        "kp_index": latest.get("kp_index"),
                        "estimated_kp": latest.get("estimated_kp"),
                        "kp": latest.get("kp"),
                        "source": "NOAA_SWPC_PLANETARY_FALLBACK"
                    }
                    
                    logger.info(f"Successfully fetched fallback Kp-index: {result['kp_index']}")
                    return result
                    
            except Exception as fallback_error:
                logger.error(f"Fallback Kp-index data also failed: {str(fallback_error)}")
            
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
