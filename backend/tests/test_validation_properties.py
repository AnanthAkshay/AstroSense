"""
Property-based tests for Validation Engine
Tests universal properties for data validation
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from services.validation import ValidationEngine, ValidationError


# Custom strategies for space weather data
@st.composite
def valid_space_weather_data(draw):
    """Generate valid space weather data"""
    return {
        "timestamp": draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )).isoformat(),
        "solar_wind_speed": draw(st.floats(min_value=200.0, max_value=1000.0)),
        "bz_field": draw(st.floats(min_value=-100.0, max_value=100.0)),
        "kp_index": draw(st.floats(min_value=0.0, max_value=9.0)),
        "proton_flux": draw(st.floats(min_value=0.0, max_value=1e6)),
        "source": draw(st.sampled_from(["NASA_DONKI", "NOAA_SWPC"]))
    }


@st.composite
def incomplete_space_weather_data(draw):
    """Generate incomplete space weather data (missing required fields)"""
    data = {
        "solar_wind_speed": draw(st.floats(min_value=200.0, max_value=1000.0)),
        "bz_field": draw(st.floats(min_value=-100.0, max_value=100.0)),
    }
    # Randomly omit required fields
    if draw(st.booleans()):
        data["timestamp"] = draw(st.datetimes()).isoformat()
    if draw(st.booleans()):
        data["source"] = draw(st.sampled_from(["NASA_DONKI", "NOAA_SWPC"]))
    return data


@st.composite
def out_of_range_data(draw):
    """Generate data with values outside valid ranges"""
    field = draw(st.sampled_from([
        "solar_wind_speed", "bz_field", "kp_index", "proton_flux"
    ]))
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "source": "TEST"
    }
    
    # Generate out-of-range value
    if field == "solar_wind_speed":
        data[field] = draw(st.one_of(
            st.floats(min_value=-1000, max_value=199.9),
            st.floats(min_value=1000.1, max_value=5000)
        ))
    elif field == "bz_field":
        data[field] = draw(st.one_of(
            st.floats(min_value=-500, max_value=-100.1),
            st.floats(min_value=100.1, max_value=500)
        ))
    elif field == "kp_index":
        data[field] = draw(st.one_of(
            st.floats(min_value=-5, max_value=-0.1),
            st.floats(min_value=9.1, max_value=20)
        ))
    elif field == "proton_flux":
        data[field] = draw(st.floats(min_value=1e6 + 1, max_value=1e10))
    
    return data, field


@st.composite
def chronological_timestamps(draw):
    """Generate list of chronologically ordered timestamps"""
    num_records = draw(st.integers(min_value=2, max_value=20))
    base_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2024, 1, 1)
    ))
    
    records = []
    current_time = base_time
    for _ in range(num_records):
        records.append({
            "timestamp": current_time.isoformat(),
            "source": "TEST",
            "value": draw(st.floats(min_value=0, max_value=100))
        })
        # Increment by 1-60 minutes
        current_time += timedelta(minutes=draw(st.integers(min_value=1, max_value=60)))
    
    return records


# Feature: astrosense-space-weather, Property 73: Required field validation
@pytest.mark.property
@given(data=incomplete_space_weather_data())
@settings(max_examples=100, deadline=None)
def test_property_73_required_field_validation(data):
    """
    Property 73: Required field validation
    For any data received from external APIs, the validation engine should
    verify that all required fields are present
    
    Validates: Requirements 20.1
    """
    engine = ValidationEngine()
    
    # When we validate incomplete data
    result = engine.validate_completeness(data, "space_weather_data")
    
    # Then validation should fail if any required field is missing
    required_fields = ["timestamp", "source"]
    has_all_required = all(field in data and data[field] is not None for field in required_fields)
    
    if has_all_required:
        assert result == True, "Should pass when all required fields present"
    else:
        assert result == False, "Should fail when required fields missing"
        assert len(engine.validation_failures) > 0, "Should log validation failure"


# Feature: astrosense-space-weather, Property 74: Numerical range validation
@pytest.mark.property
@given(data_and_field=out_of_range_data())
@settings(max_examples=100, deadline=None)
def test_property_74_numerical_range_validation(data_and_field):
    """
    Property 74: Numerical range validation
    For any numerical value in received data, the validation engine should
    reject values outside physically plausible ranges
    
    Validates: Requirements 20.2
    """
    data, field = data_and_field
    engine = ValidationEngine()
    
    # When we validate data with out-of-range values
    result = engine.validate_ranges(data)
    
    # Then validation should fail
    assert result == False, f"Should reject out-of-range {field}"
    assert len(engine.validation_failures) > 0, "Should log validation failure"
    
    # Verify the failure was logged with correct type
    assert any(f["failure_type"] == "range" for f in engine.validation_failures), \
        "Should log range validation failure"


# Feature: astrosense-space-weather, Property 75: Validation failure logging
@pytest.mark.property
@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.integers(), st.floats(), st.text(max_size=50))
    )
)
@settings(max_examples=100, deadline=None)
def test_property_75_validation_failure_logging(data):
    """
    Property 75: Validation failure logging
    For any data validation failure, the system should log the error
    with details and skip the invalid record
    
    Validates: Requirements 20.3
    """
    engine = ValidationEngine()
    initial_failure_count = len(engine.validation_failures)
    
    # When we validate data that will likely fail
    result = engine.validate_completeness(data, "space_weather_data")
    
    # If validation failed
    if not result:
        # Then a failure should be logged
        assert len(engine.validation_failures) > initial_failure_count, \
            "Should log validation failure"
        
        # And the log should contain required information
        latest_failure = engine.validation_failures[-1]
        assert "timestamp" in latest_failure, "Failure log should have timestamp"
        assert "failure_type" in latest_failure, "Failure log should have type"
        assert "message" in latest_failure, "Failure log should have message"
        assert "data_sample" in latest_failure, "Failure log should have data sample"


# Feature: astrosense-space-weather, Property 76: Timestamp chronology validation
@pytest.mark.property
@given(records=chronological_timestamps())
@settings(max_examples=100, deadline=None)
def test_property_76_timestamp_chronology_validation(records):
    """
    Property 76: Timestamp chronology validation
    For any sequence of data records, the validation engine should verify
    that timestamps are in chronological order
    
    Validates: Requirements 20.4
    """
    engine = ValidationEngine()
    
    # When we validate chronologically ordered records
    result = engine.validate_timestamps(records)
    
    # Then validation should pass
    assert result == True, "Should pass for chronologically ordered timestamps"
    
    # Now test with reversed order (should fail)
    reversed_records = list(reversed(records))
    if len(reversed_records) > 1:
        result_reversed = engine.validate_timestamps(reversed_records)
        assert result_reversed == False, "Should fail for non-chronological timestamps"


# Feature: astrosense-space-weather, Property 77: Data quality alerting
@pytest.mark.property
@given(
    num_valid=st.integers(min_value=0, max_value=50),
    num_invalid=st.integers(min_value=0, max_value=50)
)
@settings(max_examples=100, deadline=None)
def test_property_77_data_quality_alerting(num_valid, num_invalid):
    """
    Property 77: Data quality alerting
    For any time period where data completeness falls below 90 percent,
    the system should track the quality metric and generate an alert
    
    Validates: Requirements 20.5
    """
    assume(num_valid + num_invalid > 0)  # Need at least one record
    
    engine = ValidationEngine()
    engine.reset_metrics()
    
    # Simulate validation of records
    for _ in range(num_valid):
        engine.data_quality_metrics["total_records"] += 1
        engine.data_quality_metrics["valid_records"] += 1
    
    for _ in range(num_invalid):
        engine.data_quality_metrics["total_records"] += 1
        engine.data_quality_metrics["invalid_records"] += 1
    
    # When we check quality metrics
    metrics = engine.get_quality_metrics()
    
    # Then completeness percentage should be calculated correctly
    expected_completeness = (num_valid / (num_valid + num_invalid)) * 100
    assert abs(metrics["completeness_percentage"] - expected_completeness) < 0.01, \
        "Completeness percentage should be accurate"
    
    # And quality threshold check should work correctly
    threshold_result = engine.check_quality_threshold(90.0)
    
    if expected_completeness >= 90.0:
        assert threshold_result == True, "Should pass when quality >= 90%"
    else:
        assert threshold_result == False, "Should fail when quality < 90%"


# Additional property tests for edge cases
@pytest.mark.property
@given(valid_data=valid_space_weather_data())
@settings(max_examples=100, deadline=None)
def test_valid_data_passes_all_validations(valid_data):
    """Test that valid data passes all validation checks"""
    engine = ValidationEngine()
    
    # Completeness check
    assert engine.validate_completeness(valid_data) == True
    
    # Range check
    assert engine.validate_ranges(valid_data) == True
    
    # Full record validation
    assert engine.validate_record(valid_data) == True


@pytest.mark.property
@given(
    flare_class=st.sampled_from(['X', 'M', 'C', 'B', 'A']),
    magnitude=st.floats(min_value=0.0, max_value=9.9)
)
@settings(max_examples=100, deadline=None)
def test_flare_class_validation(flare_class, magnitude):
    """Test flare class validation for all valid classes"""
    engine = ValidationEngine()
    
    flare_string = f"{flare_class}{magnitude:.1f}"
    result = engine.validate_flare_class(flare_string)
    
    assert result == True, f"Should validate correct flare class {flare_string}"


@pytest.mark.property
@given(invalid_class=st.text(min_size=1, max_size=5).filter(
    lambda x: x[0].upper() not in ['X', 'M', 'C', 'B', 'A']
))
@settings(max_examples=50, deadline=None)
def test_invalid_flare_class_rejected(invalid_class):
    """Test that invalid flare classes are rejected"""
    engine = ValidationEngine()
    
    result = engine.validate_flare_class(invalid_class)
    
    assert result == False, f"Should reject invalid flare class {invalid_class}"


@pytest.mark.property
def test_quality_metrics_reset():
    """Test that quality metrics can be reset"""
    engine = ValidationEngine()
    
    # Add some metrics
    engine.data_quality_metrics["total_records"] = 100
    engine.data_quality_metrics["valid_records"] = 80
    engine.validation_failures.append({"test": "failure"})
    
    # Reset
    engine.reset_metrics()
    
    # Verify reset
    assert engine.data_quality_metrics["total_records"] == 0
    assert engine.data_quality_metrics["valid_records"] == 0
    assert len(engine.validation_failures) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
