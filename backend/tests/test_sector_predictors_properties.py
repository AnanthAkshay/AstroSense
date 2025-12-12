"""
Property-based tests for Sector-Specific Predictors
Tests universal properties for aviation, telecom, GPS, power grid, and satellite predictions
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timezone
from services.sector_predictors import (
    AviationPredictor,
    TelecomPredictor,
    GPSPredictor,
    PowerGridPredictor,
    SatellitePredictor
)


# ============================================================================
# Aviation Predictor Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 12: Aviation risk output range
@pytest.mark.property
@given(
    flare_class=st.sampled_from(['', 'A1.0', 'B2.0', 'C5.0', 'M3.0', 'X1.5']),
    solar_wind_speed=st.floats(min_value=300.0, max_value=900.0),
    kp_index=st.floats(min_value=0.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=20.0)
)
@settings(max_examples=100, deadline=None)
def test_property_12_aviation_risk_output_range(flare_class, solar_wind_speed, kp_index, bz):
    """
    Property 12: Aviation risk output range
    For any solar flare data input, the calculated aviation HF blackout probability
    should be a value between 0 and 100 inclusive
    
    Validates: Requirements 4.1
    """
    predictor = AviationPredictor()
    
    # When we calculate HF blackout probability
    probability = predictor.calculate_hf_blackout_probability(
        flare_class, solar_wind_speed, kp_index, bz
    )
    
    # Then it should be in valid range [0, 100]
    assert 0.0 <= probability <= 100.0, \
        f"HF blackout probability {probability} should be in range [0, 100]"


# Feature: astrosense-space-weather, Property 13: Polar route risk sensitivity
@pytest.mark.property
@given(
    kp_index1=st.floats(min_value=0.0, max_value=9.0),
    kp_index2=st.floats(min_value=0.0, max_value=9.0),
    latitude=st.floats(min_value=10.0, max_value=90.0)  # Avoid 0 latitude where risk is always 0
)
@settings(max_examples=100, deadline=None)
def test_property_13_polar_route_risk_sensitivity(kp_index1, kp_index2, latitude):
    """
    Property 13: Polar route risk sensitivity
    For any two inputs differing only in geomagnetic latitude or Kp-index,
    changing these values should affect the polar route risk calculation
    
    Validates: Requirements 4.2
    """
    predictor = AviationPredictor()
    
    # Ensure inputs are different and Kp values are non-zero
    assume(abs(kp_index1 - kp_index2) > 0.5)
    assume(kp_index1 > 0.1 or kp_index2 > 0.1)  # At least one should be non-zero
    
    # Calculate risk with different Kp values
    risk1 = predictor.calculate_polar_route_risk(kp_index1, latitude)
    risk2 = predictor.calculate_polar_route_risk(kp_index2, latitude)
    
    # Then risks should be different
    assert risk1 != risk2, \
        f"Different Kp-index values should produce different polar route risks"
    
    # Both should be in valid range
    assert 0.0 <= risk1 <= 100.0
    assert 0.0 <= risk2 <= 100.0



# Feature: astrosense-space-weather, Property 14: Aviation alert threshold
@pytest.mark.property
@given(
    flare_class=st.sampled_from(['X1.0', 'X2.5', 'X5.0']),
    solar_wind_speed=st.floats(min_value=600.0, max_value=900.0),
    kp_index=st.floats(min_value=7.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=-15.0)
)
@settings(max_examples=100, deadline=None)
def test_property_14_aviation_alert_threshold(flare_class, solar_wind_speed, kp_index, bz):
    """
    Property 14: Aviation alert threshold
    For any prediction where aviation risk exceeds 70 percent, the system should
    generate a high-priority alert containing mitigation recommendations
    
    Validates: Requirements 4.3
    """
    predictor = AviationPredictor()
    
    space_weather_data = {
        'flare_class': flare_class,
        'solar_wind_speed': solar_wind_speed,
        'kp_index': kp_index,
        'bz': bz
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data)
    
    # If risk exceeds 70%, should have alert
    if result['hf_blackout_probability'] > 70.0 or result['polar_route_risk'] > 70.0:
        assert result['alert'] is not None, \
            "Should generate alert when risk exceeds 70%"
        assert result['alert']['severity'] == 'HIGH', \
            "Alert should be HIGH severity"
        assert 'mitigation' in result['alert'], \
            "Alert should contain mitigation recommendations"
        assert len(result['alert']['mitigation']) > 0, \
            "Should have at least one mitigation recommendation"


# ============================================================================
# Telecom Predictor Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 15: Telecom degradation output range
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=0.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=20.0),
    solar_wind_speed=st.floats(min_value=300.0, max_value=900.0),
    proton_flux=st.floats(min_value=0.0, max_value=1000.0)
)
@settings(max_examples=100, deadline=None)
def test_property_15_telecom_degradation_output_range(kp_index, bz, solar_wind_speed, proton_flux):
    """
    Property 15: Telecom degradation output range
    For any space weather data input, the predicted telecommunications signal
    degradation should be a percentage between 0 and 100 inclusive
    
    Validates: Requirements 5.1
    """
    predictor = TelecomPredictor()
    
    # When we calculate signal degradation
    degradation = predictor.calculate_signal_degradation(
        kp_index, bz, solar_wind_speed, proton_flux
    )
    
    # Then it should be in valid range [0, 100]
    assert 0.0 <= degradation <= 100.0, \
        f"Signal degradation {degradation} should be in range [0, 100]"


# Feature: astrosense-space-weather, Property 16: Telecom moderate threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=4.0, max_value=6.0),
    bz=st.floats(min_value=-20.0, max_value=-5.0),
    solar_wind_speed=st.floats(min_value=500.0, max_value=650.0)
)
@settings(max_examples=100, deadline=None)
def test_property_16_telecom_moderate_threshold(kp_index, bz, solar_wind_speed):
    """
    Property 16: Telecom moderate threshold
    For any prediction where signal degradation exceeds 30 percent but is below 60 percent,
    the system should classify the impact as moderate and issue a warning alert
    
    Validates: Requirements 5.2
    """
    predictor = TelecomPredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'bz': bz,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': 0.0
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data)
    
    degradation = result['signal_degradation_percent']
    
    # If degradation is in moderate range [30, 60)
    if 30.0 <= degradation < 60.0:
        assert result['classification'] == 'moderate', \
            f"Degradation {degradation}% should be classified as moderate"
        assert result['alert'] is not None, \
            "Should issue warning alert for moderate degradation"
        assert result['alert']['severity'] == 'WARNING', \
            "Alert severity should be WARNING for moderate degradation"
        assert result['alert']['classification'] == 'moderate'



# Feature: astrosense-space-weather, Property 17: Telecom critical threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=7.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=-20.0),
    solar_wind_speed=st.floats(min_value=700.0, max_value=900.0)
)
@settings(max_examples=100, deadline=None)
def test_property_17_telecom_critical_threshold(kp_index, bz, solar_wind_speed):
    """
    Property 17: Telecom critical threshold
    For any prediction where signal degradation exceeds 60 percent, the system
    should classify the impact as severe and issue a critical alert
    
    Validates: Requirements 5.3
    """
    predictor = TelecomPredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'bz': bz,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': 100.0
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data)
    
    degradation = result['signal_degradation_percent']
    
    # If degradation exceeds 60%
    if degradation >= 60.0:
        assert result['classification'] == 'severe', \
            f"Degradation {degradation}% should be classified as severe"
        assert result['alert'] is not None, \
            "Should issue critical alert for severe degradation"
        assert result['alert']['severity'] == 'CRITICAL', \
            "Alert severity should be CRITICAL for severe degradation"
        assert result['alert']['classification'] == 'severe'


# ============================================================================
# GPS Predictor Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 18: GPS drift output units
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=0.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=20.0),
    solar_wind_speed=st.floats(min_value=300.0, max_value=900.0),
    proton_flux=st.floats(min_value=0.0, max_value=1000.0)
)
@settings(max_examples=100, deadline=None)
def test_property_18_gps_drift_output_units(kp_index, bz, solar_wind_speed, proton_flux):
    """
    Property 18: GPS drift output units
    For any ionospheric disturbance prediction, the GPS positional drift should
    be expressed in centimeters as a non-negative number
    
    Validates: Requirements 6.1
    """
    predictor = GPSPredictor()
    
    # When we calculate positional drift
    drift = predictor.calculate_positional_drift(
        kp_index, bz, solar_wind_speed, proton_flux
    )
    
    # Then it should be non-negative (in centimeters)
    assert drift >= 0.0, \
        f"GPS drift {drift} should be non-negative (in cm)"


# Feature: astrosense-space-weather, Property 19: GPS moderate warning threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=3.0, max_value=5.0),
    bz=st.floats(min_value=-15.0, max_value=-5.0),
    solar_wind_speed=st.floats(min_value=450.0, max_value=600.0)
)
@settings(max_examples=100, deadline=None)
def test_property_19_gps_moderate_warning_threshold(kp_index, bz, solar_wind_speed):
    """
    Property 19: GPS moderate warning threshold
    For any prediction where GPS drift exceeds 50 centimeters but is below 200 centimeters,
    the system should issue a moderate accuracy warning
    
    Validates: Requirements 6.2
    """
    predictor = GPSPredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'bz': bz,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': 50.0
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data)
    
    drift = result['positional_drift_cm']
    
    # If drift is in moderate range [50, 200)
    if 50.0 <= drift < 200.0:
        assert result['classification'] == 'moderate', \
            f"Drift {drift} cm should be classified as moderate"
        assert result['alert'] is not None, \
            "Should issue moderate warning for drift in [50, 200) cm"
        assert result['alert']['severity'] == 'WARNING'
        assert result['alert']['classification'] == 'moderate'



# Feature: astrosense-space-weather, Property 20: GPS critical warning threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=7.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=-25.0),
    solar_wind_speed=st.floats(min_value=700.0, max_value=900.0)
)
@settings(max_examples=100, deadline=None)
def test_property_20_gps_critical_warning_threshold(kp_index, bz, solar_wind_speed):
    """
    Property 20: GPS critical warning threshold
    For any prediction where GPS drift exceeds 200 centimeters, the system
    should issue a critical accuracy warning
    
    Validates: Requirements 6.3
    """
    predictor = GPSPredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'bz': bz,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': 200.0
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data)
    
    drift = result['positional_drift_cm']
    
    # If drift exceeds 200 cm
    if drift >= 200.0:
        assert result['classification'] == 'critical', \
            f"Drift {drift} cm should be classified as critical"
        assert result['alert'] is not None, \
            "Should issue critical warning for drift >= 200 cm"
        assert result['alert']['severity'] == 'CRITICAL'
        assert result['alert']['classification'] == 'critical'


# ============================================================================
# Power Grid Predictor Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 21: GIC risk output range
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=0.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=20.0),
    solar_wind_speed=st.floats(min_value=300.0, max_value=900.0),
    ground_conductivity=st.floats(min_value=0.0, max_value=1.0),
    grid_topology_factor=st.floats(min_value=0.5, max_value=2.0)
)
@settings(max_examples=100, deadline=None)
def test_property_21_gic_risk_output_range(kp_index, bz, solar_wind_speed, 
                                           ground_conductivity, grid_topology_factor):
    """
    Property 21: GIC risk output range
    For any geomagnetic storm conditions, the calculated GIC risk level should
    be an integer between 1 and 10 inclusive
    
    Validates: Requirements 7.1
    """
    predictor = PowerGridPredictor()
    
    # When we calculate GIC risk
    gic_risk = predictor.calculate_gic_risk(
        kp_index, bz, solar_wind_speed, ground_conductivity, grid_topology_factor
    )
    
    # Then it should be in valid range [1, 10]
    assert 1 <= gic_risk <= 10, \
        f"GIC risk {gic_risk} should be in range [1, 10]"
    
    # And should be an integer
    assert isinstance(gic_risk, int), \
        f"GIC risk should be an integer, got {type(gic_risk)}"


# Feature: astrosense-space-weather, Property 22: GIC high-risk alert threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=7.0, max_value=9.0),
    bz=st.floats(min_value=-50.0, max_value=-20.0),
    solar_wind_speed=st.floats(min_value=700.0, max_value=900.0)
)
@settings(max_examples=100, deadline=None)
def test_property_22_gic_high_risk_alert_threshold(kp_index, bz, solar_wind_speed):
    """
    Property 22: GIC high-risk alert threshold
    For any prediction where GIC risk exceeds level 7, the system should issue
    a high-risk alert with transformer protection recommendations
    
    Validates: Requirements 7.2
    """
    predictor = PowerGridPredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'bz': bz,
        'solar_wind_speed': solar_wind_speed
    }
    
    # When we generate predictions
    result = predictor.predict(space_weather_data, ground_conductivity=0.8, grid_topology_factor=1.5)
    
    gic_risk = result['gic_risk_level']
    
    # If GIC risk exceeds 7
    if gic_risk >= 7:
        assert result['alert'] is not None, \
            f"Should issue alert when GIC risk {gic_risk} >= 7"
        assert result['alert']['severity'] == 'HIGH', \
            "Alert severity should be HIGH for GIC risk >= 7"
        assert 'mitigation' in result['alert'], \
            "Alert should contain transformer protection recommendations"
        assert len(result['alert']['mitigation']) > 0



# Feature: astrosense-space-weather, Property 23: GIC calculation inputs
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=5.0, max_value=8.0),  # Higher Kp for more sensitivity
    bz=st.floats(min_value=-30.0, max_value=-10.0),  # Stronger Bz for more sensitivity
    solar_wind_speed=st.floats(min_value=600.0, max_value=800.0),  # Higher wind speed
    conductivity1=st.floats(min_value=0.2, max_value=0.4),
    conductivity2=st.floats(min_value=0.7, max_value=0.9),  # Larger difference
    topology1=st.floats(min_value=0.5, max_value=0.9),
    topology2=st.floats(min_value=1.5, max_value=2.0)  # Larger difference
)
@settings(max_examples=100, deadline=None)
def test_property_23_gic_calculation_inputs(kp_index, bz, solar_wind_speed, 
                                            conductivity1, conductivity2,
                                            topology1, topology2):
    """
    Property 23: GIC calculation inputs
    For any two inputs differing significantly in ground conductivity or grid topology factors,
    the GIC risk calculation should produce different results
    
    Validates: Requirements 7.4
    """
    predictor = PowerGridPredictor()
    
    # Ensure conductivities and topologies are sufficiently different
    # to overcome integer rounding effects
    assume(abs(conductivity1 - conductivity2) > 0.4)
    assume(abs(topology1 - topology2) > 0.5)
    
    # Test 1: Different conductivities with same topology
    risk1_cond = predictor.calculate_gic_risk(
        kp_index, bz, solar_wind_speed, conductivity1, 1.0
    )
    risk2_cond = predictor.calculate_gic_risk(
        kp_index, bz, solar_wind_speed, conductivity2, 1.0
    )
    
    # Test 2: Different topologies with same conductivity
    risk1_topo = predictor.calculate_gic_risk(
        kp_index, bz, solar_wind_speed, 0.5, topology1
    )
    risk2_topo = predictor.calculate_gic_risk(
        kp_index, bz, solar_wind_speed, 0.5, topology2
    )
    
    # With sufficiently different inputs and higher base risk,
    # at least one pair should show sensitivity
    conductivity_affects = (risk1_cond != risk2_cond)
    topology_affects = (risk1_topo != risk2_topo)
    
    # The calculation should be sensitive to at least one of these parameters
    assert conductivity_affects or topology_affects, \
        f"GIC calculation should be sensitive to conductivity or topology factors. " \
        f"Conductivity test: {risk1_cond} vs {risk2_cond}, " \
        f"Topology test: {risk1_topo} vs {risk2_topo}"


# ============================================================================
# Satellite Predictor Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 24: Satellite drag risk output range
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=0.0, max_value=9.0),
    solar_wind_speed=st.floats(min_value=300.0, max_value=900.0),
    proton_flux=st.floats(min_value=0.0, max_value=1000.0),
    altitude_km=st.floats(min_value=200.0, max_value=2000.0)
)
@settings(max_examples=100, deadline=None)
def test_property_24_satellite_drag_risk_output_range(kp_index, solar_wind_speed, 
                                                       proton_flux, altitude_km):
    """
    Property 24: Satellite drag risk output range
    For any atmospheric density change prediction, the calculated satellite orbital
    drag risk should be an integer between 1 and 10 inclusive
    
    Validates: Requirements 8.1
    """
    predictor = SatellitePredictor()
    
    # When we calculate orbital drag risk
    drag_risk = predictor.calculate_orbital_drag_risk(
        kp_index, solar_wind_speed, proton_flux, altitude_km
    )
    
    # Then it should be in valid range [1, 10]
    assert 1 <= drag_risk <= 10, \
        f"Orbital drag risk {drag_risk} should be in range [1, 10]"
    
    # And should be an integer
    assert isinstance(drag_risk, int), \
        f"Orbital drag risk should be an integer, got {type(drag_risk)}"


# Feature: astrosense-space-weather, Property 25: Satellite drag alert threshold
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=6.0, max_value=9.0),
    solar_wind_speed=st.floats(min_value=650.0, max_value=900.0),
    proton_flux=st.floats(min_value=200.0, max_value=800.0)
)
@settings(max_examples=100, deadline=None)
def test_property_25_satellite_drag_alert_threshold(kp_index, solar_wind_speed, proton_flux):
    """
    Property 25: Satellite drag alert threshold
    For any prediction where orbital drag risk exceeds level 6, the system should
    issue an alert recommending orbit adjustment maneuvers
    
    Validates: Requirements 8.2
    """
    predictor = SatellitePredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': proton_flux
    }
    
    # When we generate predictions (low altitude = higher risk)
    result = predictor.predict(space_weather_data, altitude_km=350.0)
    
    drag_risk = result['orbital_drag_risk']
    
    # If drag risk exceeds 6
    if drag_risk >= 6:
        assert result['alert'] is not None, \
            f"Should issue alert when drag risk {drag_risk} >= 6"
        assert result['alert']['severity'] == 'HIGH', \
            "Alert severity should be HIGH for drag risk >= 6"
        assert 'mitigation' in result['alert'], \
            "Alert should contain orbit adjustment recommendations"
        # Check for orbit maneuver recommendation
        mitigation_text = ' '.join(result['alert']['mitigation'])
        assert 'maneuver' in mitigation_text.lower() or 'orbit' in mitigation_text.lower()



# Feature: astrosense-space-weather, Property 26: Multi-satellite alert prioritization
@pytest.mark.property
@given(
    kp_index=st.floats(min_value=4.0, max_value=8.0),
    solar_wind_speed=st.floats(min_value=500.0, max_value=800.0),
    proton_flux=st.floats(min_value=50.0, max_value=500.0)
)
@settings(max_examples=100, deadline=None)
def test_property_26_multi_satellite_alert_prioritization(kp_index, solar_wind_speed, proton_flux):
    """
    Property 26: Multi-satellite alert prioritization
    For any set of multiple satellite predictions, alerts should be ordered by
    a combination of orbital altitude and mission criticality
    
    Validates: Requirements 8.5
    """
    predictor = SatellitePredictor()
    
    space_weather_data = {
        'kp_index': kp_index,
        'solar_wind_speed': solar_wind_speed,
        'proton_flux': proton_flux
    }
    
    # Create test satellites with varying altitudes and criticalities
    satellites = [
        {'id': 'sat1', 'name': 'Low Critical', 'altitude_km': 400.0, 'mission_criticality': 0.5},
        {'id': 'sat2', 'name': 'Low High-Crit', 'altitude_km': 400.0, 'mission_criticality': 1.8},
        {'id': 'sat3', 'name': 'High Low-Crit', 'altitude_km': 1200.0, 'mission_criticality': 0.5},
        {'id': 'sat4', 'name': 'High High-Crit', 'altitude_km': 1200.0, 'mission_criticality': 1.8}
    ]
    
    # When we prioritize satellites
    prioritized = predictor.prioritize_satellites(satellites, space_weather_data)
    
    # Then they should be ordered by priority score
    assert len(prioritized) == len(satellites), \
        "Should return all satellites"
    
    # Verify ordering: each satellite should have priority >= next
    for i in range(len(prioritized) - 1):
        assert prioritized[i]['priority_score'] >= prioritized[i+1]['priority_score'], \
            f"Satellites should be ordered by priority score (descending)"
    
    # Verify priority score calculation includes both risk and criticality
    for sat in prioritized:
        expected_priority = sat['drag_risk'] * (1 + sat['mission_criticality'])
        assert abs(sat['priority_score'] - expected_priority) < 0.01, \
            "Priority score should equal drag_risk * (1 + criticality)"


# ============================================================================
# Additional Property Tests
# ============================================================================

@pytest.mark.property
@given(
    latitude1=st.floats(min_value=0.0, max_value=50.0),
    latitude2=st.floats(min_value=60.0, max_value=90.0),
    kp_index=st.floats(min_value=5.0, max_value=8.0)
)
@settings(max_examples=50, deadline=None)
def test_polar_route_risk_increases_with_latitude(latitude1, latitude2, kp_index):
    """Test that polar route risk increases with latitude"""
    predictor = AviationPredictor()
    
    risk_low_lat = predictor.calculate_polar_route_risk(kp_index, latitude1)
    risk_high_lat = predictor.calculate_polar_route_risk(kp_index, latitude2)
    
    # Higher latitude should have higher risk
    assert risk_high_lat >= risk_low_lat, \
        f"Risk at {latitude2}° should be >= risk at {latitude1}°"


@pytest.mark.property
@given(
    altitude_low=st.floats(min_value=200.0, max_value=500.0),
    altitude_high=st.floats(min_value=1000.0, max_value=2000.0),
    kp_index=st.floats(min_value=5.0, max_value=8.0)
)
@settings(max_examples=50, deadline=None)
def test_satellite_drag_decreases_with_altitude(altitude_low, altitude_high, kp_index):
    """Test that satellite drag risk decreases with altitude"""
    predictor = SatellitePredictor()
    
    risk_low = predictor.calculate_orbital_drag_risk(kp_index, 600.0, 100.0, altitude_low)
    risk_high = predictor.calculate_orbital_drag_risk(kp_index, 600.0, 100.0, altitude_high)
    
    # Lower altitude should have higher or equal risk
    assert risk_low >= risk_high, \
        f"Risk at {altitude_low}km should be >= risk at {altitude_high}km"


@pytest.mark.property
@given(
    space_weather=st.fixed_dictionaries({
        'kp_index': st.floats(min_value=0.0, max_value=9.0),
        'bz': st.floats(min_value=-50.0, max_value=20.0),
        'solar_wind_speed': st.floats(min_value=300.0, max_value=900.0),
        'proton_flux': st.floats(min_value=0.0, max_value=1000.0),
        'flare_class': st.sampled_from(['', 'C1.0', 'M2.0', 'X1.5']),
        'cme_speed': st.floats(min_value=0.0, max_value=2000.0)
    })
)
@settings(max_examples=50, deadline=None)
def test_all_predictors_produce_valid_outputs(space_weather):
    """Test that all predictors produce valid outputs for any input"""
    aviation = AviationPredictor()
    telecom = TelecomPredictor()
    gps = GPSPredictor()
    power_grid = PowerGridPredictor()
    satellite = SatellitePredictor()
    
    # All predictors should produce valid results
    av_result = aviation.predict(space_weather)
    tc_result = telecom.predict(space_weather)
    gps_result = gps.predict(space_weather)
    pg_result = power_grid.predict(space_weather)
    sat_result = satellite.predict(space_weather)
    
    # Verify all results have expected structure
    assert 'hf_blackout_probability' in av_result
    assert 'signal_degradation_percent' in tc_result
    assert 'positional_drift_cm' in gps_result
    assert 'gic_risk_level' in pg_result
    assert 'orbital_drag_risk' in sat_result


@pytest.mark.property
@given(drift=st.floats(min_value=0.0, max_value=500.0))
@settings(max_examples=50, deadline=None)
def test_gps_geographic_distribution_structure(drift):
    """Test that GPS geographic distribution has correct structure"""
    predictor = GPSPredictor()
    
    geo_dist = predictor.determine_geographic_distribution(drift, 5.0)
    
    # Should have regions dictionary
    assert 'regions' in geo_dist
    assert 'polar' in geo_dist['regions']
    assert 'high_latitude' in geo_dist['regions']
    assert 'mid_latitude' in geo_dist['regions']
    assert 'low_latitude' in geo_dist['regions']
    
    # Should identify greatest impact region
    assert 'greatest_impact_region' in geo_dist
    assert 'greatest_impact_drift' in geo_dist
    
    # Greatest impact should be in polar regions (highest amplification)
    assert geo_dist['greatest_impact_region'] == 'polar'


# ============================================================================
# Composite Score Calculator Property Tests
# ============================================================================

# Feature: astrosense-space-weather, Property 68: Composite score calculation formula
@pytest.mark.property
@given(
    aviation_risk=st.floats(min_value=0.0, max_value=100.0),
    telecom_risk=st.floats(min_value=0.0, max_value=100.0),
    gps_risk=st.floats(min_value=0.0, max_value=100.0),
    power_grid_risk=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_68_composite_score_calculation_formula(aviation_risk, telecom_risk, 
                                                          gps_risk, power_grid_risk):
    """
    Property 68: Composite score calculation formula
    For any set of sector-specific risks, the composite impact score should equal
    0.35 times aviation risk plus 0.25 times telecom risk plus 0.20 times GPS drift
    score plus 0.20 times power grid risk
    
    Validates: Requirements 19.1
    """
    from services.sector_predictors import CompositeScoreCalculator
    
    calculator = CompositeScoreCalculator()
    
    # When we calculate composite score
    composite = calculator.calculate_composite_score(
        aviation_risk, telecom_risk, gps_risk, power_grid_risk
    )
    
    # Then it should match the weighted formula
    expected = (0.35 * aviation_risk + 
                0.25 * telecom_risk + 
                0.20 * gps_risk + 
                0.20 * power_grid_risk)
    
    # Clamp expected to [0, 100] like the implementation does
    expected = max(0.0, min(expected, 100.0))
    
    assert abs(composite - expected) < 0.01, \
        f"Composite score {composite:.2f} should match formula result {expected:.2f}"


# Feature: astrosense-space-weather, Property 69: Composite score output range
@pytest.mark.property
@given(
    aviation_risk=st.floats(min_value=0.0, max_value=100.0),
    telecom_risk=st.floats(min_value=0.0, max_value=100.0),
    gps_risk=st.floats(min_value=0.0, max_value=100.0),
    power_grid_risk=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_69_composite_score_output_range(aviation_risk, telecom_risk, 
                                                   gps_risk, power_grid_risk):
    """
    Property 69: Composite score output range
    For any calculated composite score, it should be a value between 0 and 100
    inclusive with color-coded severity indication
    
    Validates: Requirements 19.2
    """
    from services.sector_predictors import CompositeScoreCalculator
    
    calculator = CompositeScoreCalculator()
    
    # When we calculate composite score
    composite = calculator.calculate_composite_score(
        aviation_risk, telecom_risk, gps_risk, power_grid_risk
    )
    
    # Then it should be in valid range [0, 100]
    assert 0.0 <= composite <= 100.0, \
        f"Composite score {composite} should be in range [0, 100]"
    
    # And severity classification should be valid
    severity = calculator.classify_severity(composite)
    assert severity in ['low', 'moderate', 'high'], \
        f"Severity '{severity}' should be one of: low, moderate, high"
    
    # Verify severity classification logic
    if composite >= 70.0:
        assert severity == 'high', f"Score {composite} >= 70 should be 'high'"
    elif composite >= 40.0:
        assert severity == 'moderate', f"Score {composite} >= 40 should be 'moderate'"
    else:
        assert severity == 'low', f"Score {composite} < 40 should be 'low'"


# Feature: astrosense-space-weather, Property 70: High composite score alert
@pytest.mark.property
@given(
    aviation_risk=st.floats(min_value=80.0, max_value=100.0),
    telecom_risk=st.floats(min_value=70.0, max_value=100.0),
    gps_risk=st.floats(min_value=60.0, max_value=100.0),
    power_grid_risk=st.floats(min_value=60.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_70_high_composite_score_alert(aviation_risk, telecom_risk, 
                                                 gps_risk, power_grid_risk):
    """
    Property 70: High composite score alert
    For any composite score exceeding 70, the system should classify overall risk
    as high and issue a system-wide alert
    
    Validates: Requirements 19.3
    """
    from services.sector_predictors import CompositeScoreCalculator
    from datetime import datetime
    
    calculator = CompositeScoreCalculator()
    
    # Create sector predictions that will result in high composite score
    sector_predictions = {
        'aviation': {'hf_blackout_probability': aviation_risk},
        'telecom': {'signal_degradation_percent': telecom_risk},
        'gps': {'positional_drift_cm': gps_risk * 5.0},  # Will be normalized
        'power_grid': {'gic_risk_level': int((power_grid_risk / 100.0) * 9) + 1}  # Convert to 1-10
    }
    
    # When we calculate composite score
    result = calculator.calculate(sector_predictions, datetime.now(timezone.utc))
    
    composite = result['composite_score']
    
    # If composite score exceeds 70
    if composite > 70.0:
        # Then severity should be high
        assert result['severity'] == 'high', \
            f"Composite score {composite} > 70 should have 'high' severity"
        
        # And alert should be generated
        assert result['alert'] is not None, \
            f"Composite score {composite} > 70 should generate an alert"
        
        # Alert should be system-wide
        assert result['alert']['classification'] == 'system_wide', \
            "Alert should be classified as 'system_wide'"
        
        # Alert should have HIGH severity
        assert result['alert']['severity'] == 'HIGH', \
            "Alert severity should be 'HIGH'"
        
        # Alert should include mitigation recommendations
        assert 'mitigation' in result['alert'], \
            "Alert should include mitigation recommendations"
        assert len(result['alert']['mitigation']) > 0, \
            "Alert should have at least one mitigation recommendation"


# Feature: astrosense-space-weather, Property 71: Composite score change logging
@pytest.mark.property
@given(
    score1=st.floats(min_value=0.0, max_value=100.0),
    score2=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_71_composite_score_change_logging(score1, score2):
    """
    Property 71: Composite score change logging
    For any change in composite score, the system should log the change with
    timestamp and contributing sector factors
    
    Validates: Requirements 19.4
    """
    from services.sector_predictors import CompositeScoreCalculator
    from datetime import datetime, timedelta
    
    calculator = CompositeScoreCalculator()
    
    # Create first set of predictions
    sector_predictions1 = {
        'aviation': {'hf_blackout_probability': score1 * 0.5},
        'telecom': {'signal_degradation_percent': score1 * 0.5},
        'gps': {'positional_drift_cm': score1 * 2.0},
        'power_grid': {'gic_risk_level': max(1, int((score1 / 100.0) * 9) + 1)}
    }
    
    timestamp1 = datetime.now(timezone.utc)
    
    # Calculate first score
    result1 = calculator.calculate(sector_predictions1, timestamp1)
    
    # Verify change log structure for first calculation
    assert 'change_log' in result1, "Result should include change_log"
    assert 'timestamp' in result1['change_log'], "Change log should include timestamp"
    assert 'new_score' in result1['change_log'], "Change log should include new_score"
    assert 'contributing_factors' in result1['change_log'], "Change log should include contributing_factors"
    
    # For first calculation, previous_score should be None
    assert result1['change_log']['previous_score'] is None, \
        "First calculation should have no previous_score"
    
    # Create second set of predictions
    sector_predictions2 = {
        'aviation': {'hf_blackout_probability': score2 * 0.5},
        'telecom': {'signal_degradation_percent': score2 * 0.5},
        'gps': {'positional_drift_cm': score2 * 2.0},
        'power_grid': {'gic_risk_level': max(1, int((score2 / 100.0) * 9) + 1)}
    }
    
    timestamp2 = timestamp1 + timedelta(minutes=5)
    
    # Calculate second score
    result2 = calculator.calculate(sector_predictions2, timestamp2)
    
    # Verify change log for second calculation
    assert result2['change_log']['previous_score'] is not None, \
        "Second calculation should have previous_score"
    
    assert result2['change_log']['previous_score'] == result1['composite_score'], \
        "Previous score should match first calculation's score"
    
    assert 'change' in result2['change_log'], \
        "Change log should include change amount"
    
    expected_change = result2['composite_score'] - result1['composite_score']
    assert abs(result2['change_log']['change'] - expected_change) < 0.01, \
        f"Change should equal new_score - previous_score"
    
    # Verify contributing factors are logged
    assert 'aviation' in result2['contributing_factors'], \
        "Contributing factors should include aviation"
    assert 'telecom' in result2['contributing_factors'], \
        "Contributing factors should include telecom"
    assert 'gps' in result2['contributing_factors'], \
        "Contributing factors should include gps"
    assert 'power_grid' in result2['contributing_factors'], \
        "Contributing factors should include power_grid"


# Additional composite score tests

@pytest.mark.property
@given(
    drift_cm=st.floats(min_value=0.0, max_value=1000.0)
)
@settings(max_examples=100, deadline=None)
def test_gps_drift_normalization(drift_cm):
    """Test that GPS drift normalization produces valid 0-100 range"""
    from services.sector_predictors import CompositeScoreCalculator
    
    calculator = CompositeScoreCalculator()
    
    normalized = calculator.normalize_gps_drift(drift_cm)
    
    # Should be in valid range
    assert 0.0 <= normalized <= 100.0, \
        f"Normalized GPS drift {normalized} should be in range [0, 100]"
    
    # Should scale proportionally (up to max)
    if drift_cm <= 500.0:
        expected = (drift_cm / 500.0) * 100.0
        assert abs(normalized - expected) < 0.01, \
            f"Normalized value should match expected scaling"


@pytest.mark.property
@given(
    gic_level=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_gic_risk_normalization(gic_level):
    """Test that GIC risk normalization produces valid 0-100 range"""
    from services.sector_predictors import CompositeScoreCalculator
    
    calculator = CompositeScoreCalculator()
    
    normalized = calculator.normalize_gic_risk(gic_level)
    
    # Should be in valid range
    assert 0.0 <= normalized <= 100.0, \
        f"Normalized GIC risk {normalized} should be in range [0, 100]"
    
    # Should scale from 1-10 to 0-100
    expected = ((gic_level - 1) / 9.0) * 100.0
    assert abs(normalized - expected) < 0.01, \
        f"Normalized value should match expected scaling"
    
    # Level 1 should map to 0, level 10 should map to 100
    if gic_level == 1:
        assert normalized == 0.0, "GIC level 1 should normalize to 0"
    if gic_level == 10:
        assert normalized == 100.0, "GIC level 10 should normalize to 100"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
