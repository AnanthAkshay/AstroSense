"""
Property-based tests for Feature Extraction Engine
Tests universal properties for feature extraction
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from datetime import datetime, timedelta
from services.feature_extraction import FeatureExtractor


# Custom strategies
@st.composite
def normalized_space_weather_data(draw):
    """Generate normalized space weather data"""
    return {
        "solar_wind_speed_norm": draw(st.floats(min_value=0.0, max_value=1.0)),
        "bz_field_norm": draw(st.floats(min_value=0.0, max_value=1.0)),
        "kp_index_norm": draw(st.floats(min_value=0.0, max_value=1.0)),
        "proton_flux_norm": draw(st.floats(min_value=0.0, max_value=1.0)),
        "cme_speed_norm": draw(st.floats(min_value=0.0, max_value=1.0)),
        "flare_class_encoded": draw(st.floats(min_value=0.0, max_value=6.0)),
        "bz": draw(st.floats(min_value=-100.0, max_value=100.0)),
        "speed": draw(st.floats(min_value=200.0, max_value=1000.0)),
        "latitude": draw(st.floats(min_value=-90.0, max_value=90.0)),
        "longitude": draw(st.floats(min_value=-180.0, max_value=180.0))
    }


# Feature: astrosense-space-weather, Property 5: Feature extraction completeness
@pytest.mark.property
@given(raw_data=normalized_space_weather_data())
@settings(max_examples=100, deadline=None)
def test_property_5_feature_extraction_completeness(raw_data):
    """
    Property 5: Feature extraction completeness
    For any raw training data, the feature extraction process should produce
    vectors containing all six required features: solar wind speed, Bz magnetic field,
    solar flare class, proton flux, CME speed, and Kp-index
    
    Validates: Requirements 2.1
    """
    extractor = FeatureExtractor()
    
    # When we extract features
    feature_vector = extractor.extract_features(raw_data)
    
    # Then the vector should contain all required features
    assert isinstance(feature_vector, np.ndarray), "Should return numpy array"
    
    # Verify all six core features are present (plus 6 derived features = 12 total)
    feature_names = extractor.get_feature_names()
    
    required_features = [
        "solar_wind_speed_norm",
        "bz_field_norm",
        "kp_index_norm",
        "proton_flux_norm",
        "cme_speed_norm",
        "flare_class_norm"
    ]
    
    for required in required_features:
        assert required in feature_names, f"Feature {required} should be in feature names"


# Feature: astrosense-space-weather, Property 66: Feature vector dimensionality
@pytest.mark.property
@given(raw_data=normalized_space_weather_data())
@settings(max_examples=100, deadline=None)
def test_property_66_feature_vector_dimensionality(raw_data):
    """
    Property 66: Feature vector dimensionality
    For any completed feature extraction, the output feature vector should
    have exactly 12 dimensions
    
    Validates: Requirements 18.4
    """
    extractor = FeatureExtractor()
    
    # When we extract features
    feature_vector = extractor.extract_features(raw_data)
    
    # Then the vector should have exactly 12 dimensions
    assert feature_vector.shape == (12,), \
        f"Feature vector should have shape (12,), got {feature_vector.shape}"
    assert len(feature_vector) == 12, \
        f"Feature vector should have 12 elements, got {len(feature_vector)}"
    
    # Verify feature names also has 12 entries
    feature_names = extractor.get_feature_names()
    assert len(feature_names) == 12, \
        f"Feature names should have 12 entries, got {len(feature_names)}"


# Additional property tests
@pytest.mark.property
@given(raw_data=normalized_space_weather_data())
@settings(max_examples=100, deadline=None)
def test_feature_values_in_valid_range(raw_data):
    """Test that all extracted features are in valid ranges"""
    extractor = FeatureExtractor()
    
    feature_vector = extractor.extract_features(raw_data)
    
    # All features should be in [0, 1] range (normalized)
    for i, value in enumerate(feature_vector):
        assert 0.0 <= value <= 1.0, \
            f"Feature {i} ({extractor.get_feature_names()[i]}) = {value} should be in [0, 1]"


@pytest.mark.property
@given(
    latitude1=st.floats(min_value=-90.0, max_value=90.0),
    latitude2=st.floats(min_value=-90.0, max_value=90.0)
)
@settings(max_examples=100, deadline=None)
def test_geomagnetic_latitude_factor_ordering(latitude1, latitude2):
    """Test that higher latitudes produce higher geomagnetic factors"""
    extractor = FeatureExtractor()
    
    factor1 = extractor.compute_geomagnetic_latitude_factor(latitude1)
    factor2 = extractor.compute_geomagnetic_latitude_factor(latitude2)
    
    # Higher absolute latitude should give higher factor
    if abs(latitude1) > abs(latitude2):
        assert factor1 >= factor2, \
            f"Higher latitude {latitude1} should have >= factor than {latitude2}"
    elif abs(latitude1) < abs(latitude2):
        assert factor1 <= factor2, \
            f"Lower latitude {latitude1} should have <= factor than {latitude2}"


@pytest.mark.property
@given(
    measurements=st.lists(
        st.fixed_dictionaries({
            "timestamp": st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)).map(lambda d: d.isoformat()),
            "speed": st.floats(min_value=200, max_value=1000),
            "bz": st.floats(min_value=-100, max_value=100)
        }),
        min_size=1,
        max_size=50
    )
)
@settings(max_examples=50, deadline=None)
def test_historical_data_management(measurements):
    """Test that historical data is properly managed"""
    extractor = FeatureExtractor()
    
    # Add measurements
    for measurement in measurements:
        extractor.update_historical_data(measurement)
    
    # Historical data should not grow unbounded
    assert len(extractor.historical_measurements) <= len(measurements), \
        "Historical data should not exceed input size"
    
    # Should keep recent data (within 24 hours)
    if len(extractor.historical_measurements) > 0:
        for measurement in extractor.historical_measurements:
            assert "timestamp" in measurement, "Each measurement should have timestamp"


@pytest.mark.property
@given(
    current_bz=st.floats(min_value=-100.0, max_value=100.0),
    historical_bz=st.lists(
        st.floats(min_value=-100.0, max_value=100.0),
        min_size=5,
        max_size=20
    )
)
@settings(max_examples=50, deadline=None)
def test_bz_rate_of_change_calculation(current_bz, historical_bz):
    """Test Bz rate of change calculation"""
    extractor = FeatureExtractor()
    
    # Set up historical data
    base_time = datetime.now() - timedelta(hours=1)
    for i, bz_val in enumerate(historical_bz):
        measurement = {
            "timestamp": (base_time + timedelta(minutes=i * 5)).isoformat(),
            "bz": bz_val
        }
        extractor.update_historical_data(measurement)
    
    # Calculate rate of change
    rate = extractor.compute_bz_rate_of_change(current_bz, lookback_minutes=30)
    
    # Rate should be a finite number
    assert isinstance(rate, float), "Rate should be a float"
    assert not np.isnan(rate), "Rate should not be NaN"
    assert not np.isinf(rate), "Rate should not be infinite"


@pytest.mark.property
@given(
    speeds=st.lists(
        st.floats(min_value=200.0, max_value=1000.0),
        min_size=10,
        max_size=50
    )
)
@settings(max_examples=50, deadline=None)
def test_wind_speed_variance_calculation(speeds):
    """Test wind speed variance calculation"""
    extractor = FeatureExtractor()
    
    # Set up historical data
    base_time = datetime.now() - timedelta(hours=3)
    for i, speed in enumerate(speeds):
        measurement = {
            "timestamp": (base_time + timedelta(minutes=i * 5)).isoformat(),
            "speed": speed
        }
        extractor.update_historical_data(measurement)
    
    # Calculate variance
    variance = extractor.compute_wind_speed_variance(lookback_hours=3)
    
    # Variance should be non-negative
    assert variance >= 0.0, "Variance should be non-negative"
    assert isinstance(variance, float), "Variance should be a float"
    
    # If speeds are constant, variance should be near zero
    if len(set(speeds)) == 1:
        assert variance < 0.1, "Variance of constant values should be near zero"


@pytest.mark.property
@given(
    hours_ago=st.floats(min_value=0.0, max_value=200.0)
)
@settings(max_examples=100, deadline=None)
def test_time_since_last_flare(hours_ago):
    """Test time since last flare calculation"""
    extractor = FeatureExtractor()
    
    # Set last flare time
    flare_time = datetime.now() - timedelta(hours=hours_ago)
    extractor.update_flare_time(flare_time)
    
    # Calculate time since
    time_since = extractor.compute_time_since_last_flare()
    
    # Should be close to hours_ago (capped at 168)
    expected = min(hours_ago, 168.0)
    assert abs(time_since - expected) < 1.0, \
        f"Time since flare should be ~{expected}, got {time_since}"


@pytest.mark.property
@given(
    hours_until=st.floats(min_value=-10.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_cme_arrival_proximity(hours_until):
    """Test CME arrival proximity calculation"""
    extractor = FeatureExtractor()
    
    # Set CME arrival time
    arrival_time = datetime.now() + timedelta(hours=hours_until)
    extractor.update_cme_arrival(arrival_time)
    
    # Calculate proximity
    proximity = extractor.compute_cme_arrival_proximity()
    
    # Proximity should be in [0, 1]
    assert 0.0 <= proximity <= 1.0, \
        f"Proximity should be in [0, 1], got {proximity}"
    
    # If CME has arrived (hours_until <= 0), proximity should be 1.0
    if hours_until <= 0:
        assert proximity == 1.0, "Proximity should be 1.0 for arrived CME"
    
    # If CME is far away (> 72 hours), proximity should be near 0
    if hours_until > 72:
        assert proximity < 0.1, "Proximity should be near 0 for distant CME"


@pytest.mark.property
@given(
    longitude=st.floats(min_value=-180.0, max_value=180.0)
)
@settings(max_examples=100, deadline=None)
def test_local_time_factor(longitude):
    """Test local time factor calculation"""
    extractor = FeatureExtractor()
    
    # Calculate local time factor
    factor = extractor.compute_local_time_factor(longitude)
    
    # Factor should be in [0, 1]
    assert 0.0 <= factor <= 1.0, \
        f"Local time factor should be in [0, 1], got {factor}"
    assert isinstance(factor, float), "Factor should be a float"


@pytest.mark.property
def test_feature_extraction_deterministic():
    """Test that feature extraction is deterministic for same input"""
    extractor1 = FeatureExtractor()
    extractor2 = FeatureExtractor()
    
    data = {
        "solar_wind_speed_norm": 0.5,
        "bz_field_norm": 0.3,
        "kp_index_norm": 0.4,
        "proton_flux_norm": 0.2,
        "cme_speed_norm": 0.1,
        "flare_class_encoded": 3.0,
        "bz": 0.0,
        "speed": 400.0,
        "latitude": 45.0,
        "longitude": 0.0
    }
    
    features1 = extractor1.extract_features(data)
    features2 = extractor2.extract_features(data)
    
    # Should produce identical results
    np.testing.assert_array_almost_equal(features1, features2, decimal=5,
        err_msg="Feature extraction should be deterministic")


@pytest.mark.property
def test_feature_names_match_vector_length():
    """Test that feature names list matches vector dimensionality"""
    extractor = FeatureExtractor()
    
    feature_names = extractor.get_feature_names()
    
    data = {
        "solar_wind_speed_norm": 0.5,
        "bz_field_norm": 0.5,
        "kp_index_norm": 0.5,
        "proton_flux_norm": 0.5,
        "cme_speed_norm": 0.5,
        "flare_class_encoded": 3.0,
        "bz": 0.0,
        "speed": 400.0,
        "latitude": 0.0,
        "longitude": 0.0
    }
    
    feature_vector = extractor.extract_features(data)
    
    assert len(feature_names) == len(feature_vector), \
        "Number of feature names should match vector length"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
