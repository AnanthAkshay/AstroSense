"""
Property-based tests for Alert Management System
Tests universal properties for alert generation, prioritization, and lifecycle
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone, timezone, timedelta
import time

from services.alert_manager import AlertManager
from models.alert import Alert, FlashAlert, ImpactForecast, AlertType, AlertSeverity


# Custom strategies for alert testing
@st.composite
def flare_class_strategy(draw):
    """Generate valid solar flare classifications"""
    class_letter = draw(st.sampled_from(['X', 'M', 'C', 'B', 'A']))
    magnitude = draw(st.floats(min_value=1.0, max_value=99.9))
    return f"{class_letter}{magnitude:.1f}"


@st.composite
def x_class_flare_strategy(draw):
    """Generate X-class solar flare classifications"""
    magnitude = draw(st.floats(min_value=1.0, max_value=99.9))
    return f"X{magnitude:.1f}"


@st.composite
def space_weather_data_strategy(draw):
    """Generate valid space weather data"""
    return {
        'solar_wind_speed': draw(st.floats(min_value=200.0, max_value=1500.0)),
        'bz': draw(st.floats(min_value=-50.0, max_value=50.0)),
        'kp_index': draw(st.floats(min_value=0.0, max_value=9.0)),
        'proton_flux': draw(st.floats(min_value=0.0, max_value=10000.0)),
        'flare_class': draw(st.one_of(flare_class_strategy(), st.just(''))),
        'cme_speed': draw(st.floats(min_value=0.0, max_value=3000.0))
    }


@st.composite
def cme_data_strategy(draw):
    """Generate valid CME data"""
    detection_time = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2025, 12, 31)
    ))
    return {
        'cme_speed': draw(st.floats(min_value=300.0, max_value=3000.0)),
        'detection_time': detection_time,
        'cme_id': draw(st.text(min_size=10, max_size=50))
    }


@st.composite
def sector_predictions_strategy(draw):
    """Generate valid sector predictions"""
    return {
        'aviation': {
            'hf_blackout_probability': draw(st.floats(min_value=0.0, max_value=100.0)),
            'polar_route_risk': draw(st.floats(min_value=0.0, max_value=100.0))
        },
        'telecom': {
            'signal_degradation_percent': draw(st.floats(min_value=0.0, max_value=100.0))
        },
        'gps': {
            'positional_drift_cm': draw(st.floats(min_value=0.0, max_value=500.0))
        },
        'power_grid': {
            'gic_risk_level': draw(st.integers(min_value=1, max_value=10))
        },
        'satellite': {
            'orbital_drag_risk': draw(st.integers(min_value=1, max_value=10))
        }
    }


# Feature: astrosense-space-weather, Property 34: Flash alert generation speed
@pytest.mark.property
@given(
    flare_class=x_class_flare_strategy(),
    space_weather_data=space_weather_data_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_34_flash_alert_generation_speed(flare_class, space_weather_data):
    """
    Property 34: Flash alert generation speed
    For any detected X-class solar flare, the system should generate a flash alert
    within 10 seconds of detection
    
    Validates: Requirements 11.1
    """
    # Given an X-class flare detection
    manager = AlertManager()
    detection_time = datetime.now(timezone.utc)
    generation_start = datetime.now(timezone.utc)
    
    # When we generate a flash alert
    start_time = time.time()
    flash_alert = manager.generate_flash_alert(
        flare_class=flare_class,
        detection_time=detection_time,
        space_weather_data=space_weather_data,
        generation_start_time=generation_start
    )
    end_time = time.time()
    
    # Then the alert should be generated within 10 seconds
    generation_time = end_time - start_time
    assert generation_time < 10.0, f"Flash alert generation took {generation_time:.3f}s, must be < 10s"
    
    # And the alert should be a FlashAlert
    assert isinstance(flash_alert, FlashAlert), "Generated alert must be a FlashAlert"
    assert flash_alert.alert_type == AlertType.FLASH, "Alert type must be FLASH"


# Feature: astrosense-space-weather, Property 35: Flash alert content completeness
@pytest.mark.property
@given(
    flare_class=x_class_flare_strategy(),
    space_weather_data=space_weather_data_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_35_flash_alert_content_completeness(flare_class, space_weather_data):
    """
    Property 35: Flash alert content completeness
    For any generated flash alert, it should include flare classification,
    detection time, and a list of affected sectors
    
    Validates: Requirements 11.3
    """
    # Given an X-class flare
    manager = AlertManager()
    detection_time = datetime.now(timezone.utc)
    
    # When we generate a flash alert
    flash_alert = manager.generate_flash_alert(
        flare_class=flare_class,
        detection_time=detection_time,
        space_weather_data=space_weather_data
    )
    
    # Then the alert must contain all required fields
    assert flash_alert.metadata.get('flare_class') == flare_class, \
        "Alert must include flare classification"
    
    assert 'detection_time' in flash_alert.metadata, \
        "Alert must include detection time"
    
    assert len(flash_alert.affected_sectors) > 0, \
        "Alert must include list of affected sectors"
    
    # Verify alert has title and description
    assert flash_alert.title, "Alert must have a title"
    assert flash_alert.description, "Alert must have a description"
    assert flare_class in flash_alert.title or flare_class in flash_alert.description, \
        "Flare class must appear in title or description"


# Feature: astrosense-space-weather, Property 36: Alert prioritization and ordering
@pytest.mark.property
@given(
    num_alerts=st.integers(min_value=2, max_value=20),
    space_weather_data=space_weather_data_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_36_alert_prioritization_and_ordering(num_alerts, space_weather_data):
    """
    Property 36: Alert prioritization and ordering
    For any set of multiple flash alerts, they should be sorted first by severity level
    then by chronological order
    
    Validates: Requirements 11.4
    """
    # Given multiple alerts with different severities and times
    manager = AlertManager()
    
    # Generate alerts with varying severities
    flare_classes = ['X10.0', 'X5.0', 'M8.0', 'M2.0', 'C5.0']
    
    for i in range(min(num_alerts, len(flare_classes))):
        # Add small delay to ensure different timestamps
        time.sleep(0.001)
        manager.generate_flash_alert(
            flare_class=flare_classes[i % len(flare_classes)],
            detection_time=datetime.now(timezone.utc),
            space_weather_data=space_weather_data
        )
    
    # When we prioritize the alerts
    prioritized = manager.prioritize_alerts()
    
    # Then alerts should be sorted by severity first
    severity_order = {
        AlertSeverity.CRITICAL: 5,
        AlertSeverity.HIGH: 4,
        AlertSeverity.WARNING: 3,
        AlertSeverity.MODERATE: 2,
        AlertSeverity.LOW: 1
    }
    
    for i in range(len(prioritized) - 1):
        current_severity = severity_order.get(prioritized[i].severity, 0)
        next_severity = severity_order.get(prioritized[i + 1].severity, 0)
        
        # Current alert should have equal or higher severity than next
        assert current_severity >= next_severity, \
            f"Alerts not properly sorted by severity: {prioritized[i].severity} before {prioritized[i+1].severity}"
        
        # If same severity, should be chronologically ordered (older first)
        if current_severity == next_severity:
            assert prioritized[i].created_at <= prioritized[i + 1].created_at, \
                "Alerts with same severity must be chronologically ordered"


# Feature: astrosense-space-weather, Property 37: Alert expiration lifecycle
@pytest.mark.property
@given(
    flare_class=x_class_flare_strategy(),
    space_weather_data=space_weather_data_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_37_alert_expiration_lifecycle(flare_class, space_weather_data):
    """
    Property 37: Alert expiration lifecycle
    For any flash alert created, it should be moved to the alert history section
    exactly 2 hours after creation
    
    Validates: Requirements 11.5
    """
    # Given a flash alert
    manager = AlertManager()
    detection_time = datetime.now(timezone.utc)
    
    flash_alert = manager.generate_flash_alert(
        flare_class=flare_class,
        detection_time=detection_time,
        space_weather_data=space_weather_data
    )
    
    # Verify alert is active initially
    assert len(manager.active_alerts) == 1, "Alert should be in active list"
    assert len(manager.alert_history) == 0, "History should be empty initially"
    
    # When we check expiration before 2 hours
    current_time = flash_alert.created_at + timedelta(hours=1, minutes=59)
    expired_count = manager.expire_old_alerts(current_time)
    
    # Then alert should still be active
    assert expired_count == 0, "No alerts should expire before 2 hours"
    assert len(manager.active_alerts) == 1, "Alert should still be active"
    assert len(manager.alert_history) == 0, "History should still be empty"
    
    # When we check expiration at exactly 2 hours
    current_time = flash_alert.created_at + timedelta(hours=2)
    expired_count = manager.expire_old_alerts(current_time)
    
    # Then alert should be moved to history
    assert expired_count == 1, "Alert should expire at 2 hours"
    assert len(manager.active_alerts) == 0, "Active alerts should be empty"
    assert len(manager.alert_history) == 1, "Alert should be in history"
    assert manager.alert_history[0].alert_id == flash_alert.alert_id, \
        "Expired alert should match original alert"


# Feature: astrosense-space-weather, Property 38: CME forecast confidence interval
@pytest.mark.property
@given(
    cme_data=cme_data_strategy(),
    space_weather_data=space_weather_data_strategy(),
    sector_predictions=sector_predictions_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_38_cme_forecast_confidence_interval(
    cme_data, space_weather_data, sector_predictions
):
    """
    Property 38: CME forecast confidence interval
    For any detected CME, the Earth arrival time prediction should include
    a confidence interval with both lower and upper bounds
    
    Validates: Requirements 12.1
    """
    # Given a CME detection
    manager = AlertManager()
    
    # When we create an impact forecast
    forecast = manager.create_impact_forecast(
        cme_data=cme_data,
        space_weather_data=space_weather_data,
        sector_predictions=sector_predictions
    )
    
    # Then the forecast must include confidence interval
    assert 'arrival_time_lower' in forecast.metadata, \
        "Forecast must include lower bound of arrival time"
    
    assert 'arrival_time_upper' in forecast.metadata, \
        "Forecast must include upper bound of arrival time"
    
    assert 'confidence_percent' in forecast.metadata, \
        "Forecast must include confidence percentage"
    
    # Verify bounds are valid
    lower = datetime.fromisoformat(forecast.metadata['arrival_time_lower'])
    upper = datetime.fromisoformat(forecast.metadata['arrival_time_upper'])
    
    assert lower < upper, "Lower bound must be before upper bound"
    
    # Verify confidence is in valid range
    confidence = forecast.metadata['confidence_percent']
    assert 0.0 <= confidence <= 100.0, \
        f"Confidence must be between 0 and 100, got {confidence}"


# Feature: astrosense-space-weather, Property 39: Impact forecast content completeness
@pytest.mark.property
@given(
    cme_data=cme_data_strategy(),
    space_weather_data=space_weather_data_strategy(),
    sector_predictions=sector_predictions_strategy()
)
@settings(max_examples=100, deadline=None)
def test_property_39_impact_forecast_content_completeness(
    cme_data, space_weather_data, sector_predictions
):
    """
    Property 39: Impact forecast content completeness
    For any generated impact forecast, it should include predicted Kp-index,
    sector-specific impact predictions, and mitigation recommendations
    
    Validates: Requirements 12.2
    """
    # Given a CME detection
    manager = AlertManager()
    
    # When we create an impact forecast
    forecast = manager.create_impact_forecast(
        cme_data=cme_data,
        space_weather_data=space_weather_data,
        sector_predictions=sector_predictions
    )
    
    # Then the forecast must include predicted Kp-index
    assert 'predicted_kp_index' in forecast.metadata, \
        "Forecast must include predicted Kp-index"
    
    predicted_kp = forecast.metadata['predicted_kp_index']
    assert 0.0 <= predicted_kp <= 9.0, \
        f"Predicted Kp-index must be between 0 and 9, got {predicted_kp}"
    
    # Must include sector-specific impacts
    assert 'sector_impacts' in forecast.metadata, \
        "Forecast must include sector-specific impact predictions"
    
    sector_impacts = forecast.metadata['sector_impacts']
    assert isinstance(sector_impacts, dict), \
        "Sector impacts must be a dictionary"
    
    # Must include mitigation recommendations (unless no sectors are affected)
    if len(forecast.affected_sectors) > 0:
        assert len(forecast.mitigation_recommendations) > 0, \
            "Forecast with affected sectors must include mitigation recommendations"
    
    # Verify forecast has title and description
    assert forecast.title, "Forecast must have a title"
    assert forecast.description, "Forecast must have a description"
    
    # Verify affected sectors are listed (unless all predictions are at minimum)
    # It's valid to have no affected sectors if all risks are minimal
    assert isinstance(forecast.affected_sectors, list), \
        "Forecast must have affected_sectors as a list"


# Additional edge case tests
@pytest.mark.property
@given(
    flare_class=st.sampled_from(['M5.0', 'C8.0', 'B2.0']),  # Non-X-class flares
    space_weather_data=space_weather_data_strategy()
)
@settings(max_examples=50, deadline=None)
def test_flash_alert_handles_non_x_class_flares(flare_class, space_weather_data):
    """
    Test that flash alerts can be generated for non-X-class flares
    (though they may have lower severity)
    """
    manager = AlertManager()
    detection_time = datetime.now(timezone.utc)
    
    # Should not raise an error
    flash_alert = manager.generate_flash_alert(
        flare_class=flare_class,
        detection_time=detection_time,
        space_weather_data=space_weather_data
    )
    
    # Alert should be created with appropriate severity
    assert flash_alert is not None
    assert flash_alert.severity in [AlertSeverity.LOW, AlertSeverity.MODERATE, 
                                     AlertSeverity.WARNING, AlertSeverity.HIGH]


@pytest.mark.property
@given(
    num_forecasts=st.integers(min_value=1, max_value=10),
    cme_data=cme_data_strategy(),
    space_weather_data=space_weather_data_strategy(),
    sector_predictions=sector_predictions_strategy()
)
@settings(max_examples=50, deadline=None)
def test_multiple_forecasts_management(
    num_forecasts, cme_data, space_weather_data, sector_predictions
):
    """
    Test that multiple impact forecasts can be managed simultaneously
    """
    manager = AlertManager()
    
    # Create multiple forecasts
    for _ in range(num_forecasts):
        time.sleep(0.001)  # Ensure different timestamps
        manager.create_impact_forecast(
            cme_data=cme_data,
            space_weather_data=space_weather_data,
            sector_predictions=sector_predictions
        )
    
    # Verify all forecasts are active
    active_alerts = manager.get_active_alerts(prioritized=False)
    assert len(active_alerts) == num_forecasts, \
        f"Expected {num_forecasts} active alerts, got {len(active_alerts)}"
    
    # Verify prioritization works with multiple forecasts
    prioritized = manager.prioritize_alerts()
    assert len(prioritized) == num_forecasts, \
        "Prioritized list should contain all alerts"
