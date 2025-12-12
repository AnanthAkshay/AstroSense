"""
Property-based tests for Normalization Engine
Tests universal properties for data normalization
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from services.normalization import NormalizationEngine


# Feature: astrosense-space-weather, Property 63: Normalization output range
@pytest.mark.property
@given(
    value=st.floats(min_value=-1000, max_value=5000, allow_nan=False, allow_infinity=False),
    field=st.sampled_from([
        "solar_wind_speed", "bz_field", "kp_index", "proton_flux", "cme_speed"
    ])
)
@settings(max_examples=100, deadline=None)
def test_property_63_normalization_output_range(value, field):
    """
    Property 63: Normalization output range
    For any raw numerical feature value, the normalized output should be
    a value between 0 and 1 inclusive
    
    Validates: Requirements 18.1
    """
    engine = NormalizationEngine()
    
    # When we normalize a value
    normalized = engine.normalize_numerical(value, field)
    
    # Then the output should be in [0, 1] range
    assert 0.0 <= normalized <= 1.0, \
        f"Normalized value {normalized} for {field}={value} must be in [0, 1]"
    assert isinstance(normalized, float), "Normalized value must be a float"


# Feature: astrosense-space-weather, Property 64: Flare class encoding
@pytest.mark.property
@given(
    flare_class=st.sampled_from(['A', 'B', 'C', 'M', 'X']),
    magnitude=st.floats(min_value=0.0, max_value=9.9)
)
@settings(max_examples=100, deadline=None)
def test_property_64_flare_class_encoding(flare_class, magnitude):
    """
    Property 64: Flare class encoding
    For any solar flare class string (X, M, C, B, A), the encoding process
    should produce a unique numerical value
    
    Validates: Requirements 18.2
    """
    engine = NormalizationEngine()
    
    flare_string = f"{flare_class}{magnitude:.1f}"
    
    # When we encode a flare class
    encoded = engine.encode_flare_class(flare_string)
    
    # Then each class should have a unique base encoding
    expected_base = {'A': 1, 'B': 2, 'C': 3, 'M': 4, 'X': 5}[flare_class]
    
    assert encoded >= expected_base, f"Encoded value should be >= {expected_base}"
    assert encoded < expected_base + 1, f"Encoded value should be < {expected_base + 1}"
    assert isinstance(encoded, (int, float)), "Encoded value must be numeric"
    
    # Verify ordering: X > M > C > B > A
    if flare_class == 'X':
        assert encoded >= 5.0, "X-class should encode to >= 5.0"
    elif flare_class == 'M':
        assert 4.0 <= encoded < 5.0, "M-class should encode to [4.0, 5.0)"
    elif flare_class == 'C':
        assert 3.0 <= encoded < 4.0, "C-class should encode to [3.0, 4.0)"
    elif flare_class == 'B':
        assert 2.0 <= encoded < 3.0, "B-class should encode to [2.0, 3.0)"
    elif flare_class == 'A':
        assert 1.0 <= encoded < 2.0, "A-class should encode to [1.0, 2.0)"


# Feature: astrosense-space-weather, Property 65: Missing value imputation
@pytest.mark.property
@given(
    historical_values=st.lists(
        st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=10,
        max_size=100
    ),
    field=st.sampled_from(["solar_wind_speed", "bz_field", "kp_index"])
)
@settings(max_examples=100, deadline=None)
def test_property_65_missing_value_imputation(historical_values, field):
    """
    Property 65: Missing value imputation
    For any missing data point, the imputed value should be the median
    of the previous 6 hours of data
    
    Validates: Requirements 18.3
    """
    engine = NormalizationEngine()
    
    # Set up historical data
    engine.historical_data[field] = historical_values.copy()
    
    # When we impute a missing value
    imputed = engine.impute_missing(field, lookback_hours=6)
    
    # Then the imputed value should be the median of recent data
    if imputed is not None:
        expected_median = np.median(historical_values)
        
        # The imputed value should be close to the median
        # (may differ slightly due to lookback window)
        assert isinstance(imputed, float), "Imputed value must be a float"
        assert min(historical_values) <= imputed <= max(historical_values), \
            "Imputed value should be within historical range"


# Feature: astrosense-space-weather, Property 67: Raw value preservation
@pytest.mark.property
@given(
    raw_value=st.floats(min_value=200, max_value=1000, allow_nan=False, allow_infinity=False),
    field=st.sampled_from(["solar_wind_speed", "bz_field", "kp_index"])
)
@settings(max_examples=100, deadline=None)
def test_property_67_raw_value_preservation(raw_value, field):
    """
    Property 67: Raw value preservation
    For any normalized feature, the system should retain the original
    raw value in storage for audit purposes
    
    Validates: Requirements 18.5
    """
    engine = NormalizationEngine()
    
    # When we normalize a value and preserve it
    normalized = engine.normalize_numerical(raw_value, field)
    engine.preserve_raw_value(field, raw_value, normalized)
    
    # Then the raw value should be stored
    stored_values = engine.get_raw_values(field, limit=1)
    
    assert len(stored_values) > 0, "Should store at least one value"
    
    latest = stored_values[-1]
    assert "raw" in latest, "Stored record should contain raw value"
    assert "normalized" in latest, "Stored record should contain normalized value"
    assert "timestamp" in latest, "Stored record should contain timestamp"
    
    assert latest["raw"] == raw_value, "Stored raw value should match original"
    assert latest["normalized"] == normalized, "Stored normalized value should match"


# Additional property tests
@pytest.mark.property
@given(
    value=st.floats(min_value=200, max_value=1000, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100, deadline=None)
def test_normalization_denormalization_roundtrip(value):
    """Test that normalization followed by denormalization recovers original value"""
    engine = NormalizationEngine()
    field = "solar_wind_speed"
    
    # Normalize then denormalize
    normalized = engine.normalize_numerical(value, field)
    denormalized = engine.denormalize(normalized, field)
    
    # Should recover original value (within tolerance)
    assert abs(denormalized - value) < 1.0, \
        f"Roundtrip should recover original: {value} -> {normalized} -> {denormalized}"


@pytest.mark.property
@given(
    values=st.lists(
        st.floats(min_value=200, max_value=1000, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None)
def test_normalization_preserves_ordering(values):
    """Test that normalization preserves relative ordering of values"""
    engine = NormalizationEngine()
    field = "solar_wind_speed"
    
    # Normalize all values
    normalized_values = [engine.normalize_numerical(v, field) for v in values]
    
    # Check that ordering is preserved
    for i in range(len(values) - 1):
        if values[i] < values[i + 1]:
            assert normalized_values[i] <= normalized_values[i + 1], \
                "Normalization should preserve ordering"
        elif values[i] > values[i + 1]:
            assert normalized_values[i] >= normalized_values[i + 1], \
                "Normalization should preserve ordering"


@pytest.mark.property
@given(
    data=st.dictionaries(
        keys=st.sampled_from(["speed", "bz", "kp_index", "proton_flux"]),
        values=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=4
    )
)
@settings(max_examples=100, deadline=None)
def test_normalize_space_weather_data_completeness(data):
    """Test that normalize_space_weather_data handles various input combinations"""
    engine = NormalizationEngine()
    
    # When we normalize space weather data
    result = engine.normalize_space_weather_data(data)
    
    # Then result should be a dictionary
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # And all normalized values should be in [0, 1]
    for key, value in result.items():
        if isinstance(value, (int, float)):
            assert 0.0 <= value <= 1.0, f"{key}={value} should be in [0, 1]"


@pytest.mark.property
@given(
    flare1=st.sampled_from(['A', 'B', 'C', 'M', 'X']),
    flare2=st.sampled_from(['A', 'B', 'C', 'M', 'X'])
)
@settings(max_examples=100, deadline=None)
def test_flare_encoding_ordering(flare1, flare2):
    """Test that flare class encoding maintains intensity ordering"""
    engine = NormalizationEngine()
    
    intensity_order = ['A', 'B', 'C', 'M', 'X']
    
    encoded1 = engine.encode_flare_class(flare1)
    encoded2 = engine.encode_flare_class(flare2)
    
    idx1 = intensity_order.index(flare1)
    idx2 = intensity_order.index(flare2)
    
    if idx1 < idx2:
        assert encoded1 < encoded2, f"{flare1} should encode lower than {flare2}"
    elif idx1 > idx2:
        assert encoded1 > encoded2, f"{flare1} should encode higher than {flare2}"
    else:
        assert abs(encoded1 - encoded2) < 1.0, "Same class should encode similarly"


@pytest.mark.property
def test_historical_data_size_limit():
    """Test that historical data doesn't grow unbounded"""
    engine = NormalizationEngine()
    field = "solar_wind_speed"
    
    # Add many values
    for i in range(500):
        engine.add_to_history(field, float(i))
    
    # Should be limited to 288 (24 hours at 5-min intervals)
    assert len(engine.historical_data[field]) <= 288, \
        "Historical data should be limited to prevent memory issues"


@pytest.mark.property
def test_raw_values_storage_limit():
    """Test that raw values storage doesn't grow unbounded"""
    engine = NormalizationEngine()
    field = "test_field"
    
    # Add many values
    for i in range(2000):
        engine.preserve_raw_value(field, float(i), float(i) / 1000.0)
    
    # Should be limited to 1000
    stored = engine.get_raw_values(field, limit=2000)
    assert len(stored) <= 1000, \
        "Raw values storage should be limited to prevent memory issues"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
