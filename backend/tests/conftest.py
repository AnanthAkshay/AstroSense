"""
Test configuration and fixtures for AstroSense backend tests
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import httpx

# Get fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Test mode environment variable
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"


@pytest.fixture(autouse=True)
def mock_external_apis(request):
    """
    Mock external API calls to use fixtures instead of real HTTP requests
    This makes tests fast and deterministic
    """
    if not TEST_MODE:
        yield
        return
    
    # Skip mocking for tests marked with no_mock
    if hasattr(request, 'node') and request.node.get_closest_marker('no_mock'):
        yield
        return
    
    # Load fixture data
    try:
        with open(FIXTURES_DIR / "rtsw_mag_1m.json") as f:
            mag_data = json.load(f)
        with open(FIXTURES_DIR / "rtsw_wind_1m.json") as f:
            wind_data = json.load(f)
        with open(FIXTURES_DIR / "donki_cme.json") as f:
            cme_data = json.load(f)
    except FileNotFoundError:
        # Fallback minimal data if fixtures don't exist
        mag_data = [{"time_tag": "2024-01-01T00:00:00.000Z", "bz_gsm": -5.0, "bt": 6.0}]
        wind_data = [{"time_tag": "2024-01-01T00:00:00.000Z", "proton_speed": 450.0}]
        cme_data = []
    
    def mock_httpx_get(url, **kwargs):
        """Mock httpx.get calls"""
        response = MagicMock()
        response.status_code = 200
        response.raise_for_status = MagicMock()
        
        if "rtsw_mag_1m.json" in url:
            response.json.return_value = mag_data
            response.content = json.dumps(mag_data).encode()
        elif "rtsw_wind_1m.json" in url:
            response.json.return_value = wind_data
            response.content = json.dumps(wind_data).encode()
        elif "donki" in url.lower() and "cme" in url.lower():
            response.json.return_value = cme_data
            response.content = json.dumps(cme_data).encode()
        else:
            # Default empty response
            response.json.return_value = []
            response.content = b"[]"
        
        return response
    
    def mock_client_get(url, **kwargs):
        """Mock httpx.Client.get calls"""
        return mock_httpx_get(url, **kwargs)
    
    with patch('httpx.get', side_effect=mock_httpx_get), \
         patch('httpx.Client.get', side_effect=mock_client_get):
        yield


@pytest.fixture
def sample_space_weather_data():
    """Sample space weather data for testing"""
    return {
        'solar_wind_speed': 450.0,
        'bz': -5.2,
        'kp_index': 4.5,
        'proton_flux': 1500.0,
        'flare_class': 'M',
        'cme_speed': 800.0
    }


@pytest.fixture
def sample_cme_data():
    """Sample CME data for testing"""
    from datetime import datetime, timezone
    return {
        'cme_id': 'TEST-CME-001',
        'cme_speed': 850.0,
        'detection_time': datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    }


@pytest.fixture
def sample_sector_predictions():
    """Sample sector predictions for testing"""
    return {
        'aviation': {
            'hf_blackout_probability': 75.0,
            'polar_route_risk': 60.0
        },
        'telecom': {
            'signal_degradation_percent': 45.0
        },
        'gps': {
            'positional_drift_cm': 120.0
        },
        'power_grid': {
            'gic_risk_level': 7
        },
        'satellite': {
            'orbital_drag_risk': 6
        }
    }


# Set timeouts for all tests
def pytest_configure(config):
    """Configure pytest with timeouts"""
    config.addinivalue_line("markers", "timeout: mark test to run with timeout")


@pytest.fixture(autouse=True)
def fast_test_mode():
    """
    Set environment variables for faster testing
    """
    import os
    os.environ["TEST_MODE"] = "true"
    os.environ["MAX_RETRY_ATTEMPTS"] = "1"
    os.environ["BASE_BACKOFF_SECONDS"] = "0.01"
    yield
    # Cleanup not needed as env vars are process-scoped