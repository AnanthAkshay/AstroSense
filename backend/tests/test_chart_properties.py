"""
Property-based tests for chart data formatting
Tests Properties 30-33 for chart visualization requirements
"""
import pytest
from hypothesis import given, settings, strategies as st
from datetime import datetime, timedelta, timezone
from typing import List

from services.chart_data import chart_data_service, ChartSeries
from models.space_weather import SpaceWeatherData


# ==================== Test Data Generators ====================

@st.composite
def space_weather_data_generator(draw):
    """Generate valid space weather data for chart testing"""
    # Generate timestamp within last 48 hours to ensure 24-hour window coverage
    base_time = datetime.now(timezone.utc)
    hours_ago = draw(st.integers(min_value=0, max_value=48))
    timestamp = base_time - timedelta(hours=hours_ago)
    
    # Generate realistic solar wind speed (200-2000 km/s)
    solar_wind_speed = draw(st.one_of(
        st.none(),
        st.floats(min_value=200.0, max_value=2000.0, allow_nan=False, allow_infinity=False)
    ))
    
    # Generate realistic Bz field (-50 to +50 nT)
    bz_field = draw(st.one_of(
        st.none(),
        st.floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False)
    ))
    
    # Generate other fields
    kp_index = draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=9.0)))
    proton_flux = draw(st.one_of(st.none(), st.floats(min_value=0.0, max_value=1000.0)))
    source = draw(st.sampled_from(["NASA DONKI", "NOAA SWPC"]))
    
    return SpaceWeatherData(
        timestamp=timestamp,
        solar_wind_speed=solar_wind_speed,
        bz_field=bz_field,
        kp_index=kp_index,
        proton_flux=proton_flux,
        source=source
    )


@st.composite
def space_weather_data_list_generator(draw):
    """Generate list of space weather data points"""
    # Generate 10-100 data points to ensure good coverage
    data_points = draw(st.lists(
        space_weather_data_generator(),
        min_size=10,
        max_size=100
    ))
    return data_points


# ==================== Property Tests ====================

@given(data_list=space_weather_data_list_generator())
@settings(max_examples=100, deadline=None)
def test_property_30_solar_wind_chart_units(data_list):
    """
    # Feature: astrosense-space-weather, Property 30: Solar wind chart units
    
    For any solar wind data received, the time-series chart should plot 
    wind speed values in kilometers per second
    
    Validates: Requirements 10.1
    """
    # Filter to only data with solar wind speed
    wind_data = [d for d in data_list if d.solar_wind_speed is not None]
    
    if not wind_data:
        # Skip if no valid wind data
        return
    
    # Format chart data
    chart_series = chart_data_service.format_solar_wind_chart(data_list)
    
    # Verify chart series properties
    assert chart_series.name == "Solar Wind Speed"
    assert chart_series.unit == "km/s"
    
    # Verify all data points have correct unit
    for point in chart_series.data_points:
        assert point.unit == "km/s"
        # Verify value is a valid solar wind speed
        assert isinstance(point.value, (int, float))
        assert 200.0 <= point.value <= 2000.0  # Realistic range


@given(data_list=space_weather_data_list_generator())
@settings(max_examples=100, deadline=None)
def test_property_31_bz_chart_units(data_list):
    """
    # Feature: astrosense-space-weather, Property 31: Bz chart units
    
    For any Bz magnetic field data received, the time-series chart should 
    plot Bz values in nanoteslas
    
    Validates: Requirements 10.2
    """
    # Filter to only data with Bz field
    bz_data = [d for d in data_list if d.bz_field is not None]
    
    if not bz_data:
        # Skip if no valid Bz data
        return
    
    # Format chart data
    chart_series = chart_data_service.format_bz_chart(data_list)
    
    # Verify chart series properties
    assert chart_series.name == "Bz Magnetic Field"
    assert chart_series.unit == "nT"
    
    # Verify all data points have correct unit
    for point in chart_series.data_points:
        assert point.unit == "nT"
        # Verify value is a valid Bz field strength
        assert isinstance(point.value, (int, float))
        assert -50.0 <= point.value <= 50.0  # Realistic range


@given(data_list=space_weather_data_list_generator())
@settings(max_examples=100, deadline=None)
def test_property_32_chart_time_window_and_resolution(data_list):
    """
    # Feature: astrosense-space-weather, Property 32: Chart time window and resolution
    
    For any displayed chart, it should show the most recent 24 hours of data 
    with data points at 5-minute intervals
    
    Validates: Requirements 10.3
    """
    # Test both solar wind and Bz charts
    for chart_formatter in [
        chart_data_service.format_solar_wind_chart,
        chart_data_service.format_bz_chart
    ]:
        chart_series = chart_formatter(data_list)
        
        # Verify time window is 24 hours
        assert chart_series.time_window_hours == 24
        
        # Verify resolution is 5 minutes
        assert chart_series.resolution_minutes == 5
        
        # Verify data validation passes
        assert chart_data_service.validate_chart_data(chart_series)
        
        # If there are data points, verify they span at most 24 hours
        if chart_series.data_points:
            timestamps = [dp.timestamp for dp in chart_series.data_points]
            time_span = max(timestamps) - min(timestamps)
            assert time_span <= timedelta(hours=24)
            
            # Verify timestamps are sorted chronologically
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i-1]


@given(data_list=space_weather_data_list_generator())
@settings(max_examples=100, deadline=None)
def test_property_33_threshold_visualization(data_list):
    """
    # Feature: astrosense-space-weather, Property 33: Threshold visualization
    
    For any data point that crosses a critical threshold, the chart should 
    highlight the threshold line and add an annotation marking the event
    
    Validates: Requirements 10.4
    """
    # Test solar wind threshold visualization
    wind_chart = chart_data_service.format_solar_wind_chart(data_list)
    wind_annotations = chart_data_service.get_threshold_annotations(wind_chart)
    
    # Check that threshold crossings are properly annotated
    threshold_points = [p for p in wind_chart.data_points if p.threshold_crossed]
    
    for point in threshold_points:
        # Verify threshold crossing has annotation
        assert point.annotation is not None
        assert "solar wind" in point.annotation.lower()
        assert f"{point.value:.1f}" in point.annotation
        assert "km/s" in point.annotation
        
        # Verify annotation appears in annotations list
        matching_annotations = [
            a for a in wind_annotations 
            if a['timestamp'] == point.timestamp.isoformat()
        ]
        assert len(matching_annotations) == 1
        
        annotation = matching_annotations[0]
        assert annotation['value'] == point.value
        assert annotation['unit'] == "km/s"
        assert annotation['text'] == point.annotation
    
    # Test Bz threshold visualization
    bz_chart = chart_data_service.format_bz_chart(data_list)
    bz_annotations = chart_data_service.get_threshold_annotations(bz_chart)
    
    # Check that Bz threshold crossings are properly annotated
    bz_threshold_points = [p for p in bz_chart.data_points if p.threshold_crossed]
    
    for point in bz_threshold_points:
        # Verify threshold crossing has annotation
        assert point.annotation is not None
        assert "bz" in point.annotation.lower()
        assert f"{point.value:.1f}" in point.annotation
        assert "nT" in point.annotation
        
        # Verify annotation appears in annotations list
        matching_annotations = [
            a for a in bz_annotations 
            if a['timestamp'] == point.timestamp.isoformat()
        ]
        assert len(matching_annotations) == 1
        
        annotation = matching_annotations[0]
        assert annotation['value'] == point.value
        assert annotation['unit'] == "nT"
        assert annotation['text'] == point.annotation
    
    # Verify threshold values are correctly applied
    # Solar wind thresholds: moderate=500, high=700, extreme=1000
    for point in wind_chart.data_points:
        if point.value >= 1000.0:
            assert point.threshold_crossed
            assert "extreme" in point.annotation.lower()
        elif point.value >= 700.0:
            assert point.threshold_crossed
            assert "high" in point.annotation.lower()
        elif point.value >= 500.0:
            assert point.threshold_crossed
            assert "moderate" in point.annotation.lower()
    
    # Bz thresholds: moderate=-5, high=-10, extreme=-20 (negative values)
    for point in bz_chart.data_points:
        if point.value <= -20.0:
            assert point.threshold_crossed
            assert "extreme" in point.annotation.lower()
        elif point.value <= -10.0:
            assert point.threshold_crossed
            assert "high" in point.annotation.lower()
        elif point.value <= -5.0:
            assert point.threshold_crossed
            assert "moderate" in point.annotation.lower()


# ==================== Additional Helper Tests ====================

def test_chart_data_service_initialization():
    """Test that chart data service initializes correctly"""
    assert chart_data_service is not None
    assert hasattr(chart_data_service, 'SOLAR_WIND_THRESHOLDS')
    assert hasattr(chart_data_service, 'BZ_THRESHOLDS')
    
    # Verify threshold values
    assert chart_data_service.SOLAR_WIND_THRESHOLDS['moderate'] == 500.0
    assert chart_data_service.SOLAR_WIND_THRESHOLDS['high'] == 700.0
    assert chart_data_service.SOLAR_WIND_THRESHOLDS['extreme'] == 1000.0
    
    assert chart_data_service.BZ_THRESHOLDS['moderate'] == -5.0
    assert chart_data_service.BZ_THRESHOLDS['high'] == -10.0
    assert chart_data_service.BZ_THRESHOLDS['extreme'] == -20.0


def test_empty_data_handling():
    """Test that chart service handles empty data gracefully"""
    empty_data = []
    
    wind_chart = chart_data_service.format_solar_wind_chart(empty_data)
    assert wind_chart.name == "Solar Wind Speed"
    assert wind_chart.unit == "km/s"
    assert len(wind_chart.data_points) == 0
    
    bz_chart = chart_data_service.format_bz_chart(empty_data)
    assert bz_chart.name == "Bz Magnetic Field"
    assert bz_chart.unit == "nT"
    assert len(bz_chart.data_points) == 0


def test_none_values_filtering():
    """Test that None values are properly filtered out"""
    now = datetime.now(timezone.utc)
    
    # Create data with some None values
    test_data = [
        SpaceWeatherData(now, 500.0, -10.0, 5.0, 100.0, "TEST"),
        SpaceWeatherData(now, None, -5.0, 4.0, 90.0, "TEST"),  # None solar wind
        SpaceWeatherData(now, 600.0, None, 6.0, 110.0, "TEST"),  # None Bz
        SpaceWeatherData(now, None, None, 3.0, 80.0, "TEST"),   # Both None
    ]
    
    wind_chart = chart_data_service.format_solar_wind_chart(test_data)
    # Should only include points with non-None solar wind speed
    assert len(wind_chart.data_points) == 2
    
    bz_chart = chart_data_service.format_bz_chart(test_data)
    # Should only include points with non-None Bz field
    assert len(bz_chart.data_points) == 2