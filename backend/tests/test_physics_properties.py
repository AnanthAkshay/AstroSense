"""
Property-based tests for Physics Rules Engine and Fusion Combiner
Tests universal properties for physics-based predictions
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from services.physics_rules import PhysicsRulesEngine
from services.fusion_combiner import FusionCombiner


# Feature: astrosense-space-weather, Property 8: McPherron relation application
@pytest.mark.property
@given(
    bz=st.floats(min_value=-50.0, max_value=-10.0),
    wind_speed=st.floats(min_value=500.0, max_value=900.0)
)
@settings(max_examples=100, deadline=None)
def test_property_8_mcpherron_relation_application(bz, wind_speed):
    """
    Property 8: McPherron relation application
    For any input where Bz is below -10 nT AND solar wind speed exceeds 500 km/s,
    the Physics Fusion Engine should increase the storm risk prediction compared to baseline
    
    Validates: Requirements 3.1
    """
    engine = PhysicsRulesEngine()
    
    # Calculate storm risk with strong conditions
    strong_risk = engine.apply_mcpherron_relation(bz, wind_speed)
    
    # Calculate baseline risk with weaker conditions
    baseline_bz = -5.0  # Weak negative Bz
    baseline_speed = 400.0  # Moderate speed
    baseline_risk = engine.apply_mcpherron_relation(baseline_bz, baseline_speed)
    
    # Then strong conditions should produce higher risk than baseline
    assert strong_risk > baseline_risk, \
        f"Strong conditions (Bz={bz}, V={wind_speed}) should have higher risk than baseline"
    
    # Risk should be in valid range
    assert 0.0 <= strong_risk <= 1.0, "Risk should be in [0, 1] range"


# Feature: astrosense-space-weather, Property 9: High-speed CME impact amplification
@pytest.mark.property
@given(
    high_speed=st.floats(min_value=1000.0, max_value=2000.0),
    low_speed=st.floats(min_value=300.0, max_value=500.0)
)
@settings(max_examples=100, deadline=None)
def test_property_9_high_speed_cme_amplification(high_speed, low_speed):
    """
    Property 9: High-speed CME impact amplification
    For any CME with speed exceeding 1000 km/s, the predicted impact severity
    should be higher than for a CME with speed below 500 km/s, all other factors being equal
    
    Validates: Requirements 3.2
    """
    engine = PhysicsRulesEngine()
    
    # Calculate impact for high-speed CME
    high_impact = engine.calculate_cme_impact(high_speed)
    
    # Calculate impact for low-speed CME
    low_impact = engine.calculate_cme_impact(low_speed)
    
    # Then high-speed CME should have greater impact
    assert high_impact > low_impact, \
        f"High-speed CME ({high_speed} km/s) should have greater impact than low-speed ({low_speed} km/s)"
    
    # Both should be in valid range
    assert 0.0 <= high_impact <= 1.5, "High-speed impact should be in valid range"
    assert 0.0 <= low_impact <= 1.0, "Low-speed impact should be in valid range"


# Feature: astrosense-space-weather, Property 10: Fusion weighting formula
@pytest.mark.property
@given(
    ml_pred=st.floats(min_value=0.0, max_value=100.0),
    physics_pred=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_10_fusion_weighting_formula(ml_pred, physics_pred):
    """
    Property 10: Fusion weighting formula
    For any ML prediction and physics rule output, the combined fusion score
    should equal 0.6 times ML prediction plus 0.4 times physics prediction
    
    Validates: Requirements 3.4
    """
    combiner = FusionCombiner(ml_weight=0.6, physics_weight=0.4)
    
    ml_predictions = {'test_metric': ml_pred}
    physics_predictions = {'test_metric': physics_pred}
    
    # When we combine predictions
    combined = combiner.combine_predictions(ml_predictions, physics_predictions)
    
    # Then the result should follow the weighting formula
    expected = 0.6 * ml_pred + 0.4 * physics_pred
    actual = combined['test_metric']
    
    assert abs(actual - expected) < 0.01, \
        f"Combined value {actual} should equal 0.6*{ml_pred} + 0.4*{physics_pred} = {expected}"


# Feature: astrosense-space-weather, Property 11: Conservative conflict resolution
@pytest.mark.property
@given(
    ml_val=st.floats(min_value=10.0, max_value=50.0),
    physics_val=st.floats(min_value=60.0, max_value=100.0)
)
@settings(max_examples=100, deadline=None)
def test_property_11_conservative_conflict_resolution(ml_val, physics_val):
    """
    Property 11: Conservative conflict resolution
    For any pair of contradictory ML and physics predictions, the system should
    select the higher risk estimate and log the discrepancy
    
    Validates: Requirements 3.5
    """
    combiner = FusionCombiner()
    combiner.clear_discrepancy_log()
    
    # Ensure predictions are conflicting (differ by > 20)
    assume(abs(ml_val - physics_val) > 20)
    
    # When we resolve conflicts
    resolved, is_conflict = combiner.resolve_conflicts(ml_val, physics_val, 'test_field')
    
    # Then it should be flagged as a conflict
    assert is_conflict == True, "Should detect conflict when difference > 20"
    
    # And should use conservative (higher) estimate
    expected_conservative = max(ml_val, physics_val)
    assert resolved == expected_conservative, \
        f"Should use conservative estimate {expected_conservative}, got {resolved}"
    
    # And should log the discrepancy
    assert len(combiner.discrepancy_log) > 0, "Should log discrepancy"
    
    latest_log = combiner.discrepancy_log[-1]
    assert latest_log['field'] == 'test_field'
    assert latest_log['resolved_value'] == expected_conservative


# Additional property tests
@pytest.mark.property
@given(bz=st.floats(min_value=0.0, max_value=50.0))
@settings(max_examples=50, deadline=None)
def test_positive_bz_low_risk(bz):
    """Test that positive (northward) Bz produces low storm risk"""
    engine = PhysicsRulesEngine()
    
    risk = engine.apply_mcpherron_relation(bz, 600.0)
    
    # Positive Bz should produce minimal risk
    assert risk <= 0.2, f"Positive Bz={bz} should produce low risk, got {risk}"


@pytest.mark.property
@given(flare_class=st.sampled_from(['X1.0', 'X2.5', 'X5.0', 'X9.9']))
@settings(max_examples=20, deadline=None)
def test_x_class_flare_triggers_blackout(flare_class):
    """Test that all X-class flares trigger immediate blackout"""
    engine = PhysicsRulesEngine()
    
    blackout = engine.check_flare_blackout(flare_class)
    
    assert blackout == True, f"X-class flare {flare_class} should trigger blackout"


@pytest.mark.property
@given(flare_class=st.sampled_from(['M1.0', 'C5.0', 'B2.0', 'A1.0']))
@settings(max_examples=20, deadline=None)
def test_non_x_class_no_immediate_blackout(flare_class):
    """Test that non-X-class flares don't trigger immediate blackout"""
    engine = PhysicsRulesEngine()
    
    blackout = engine.check_flare_blackout(flare_class)
    
    assert blackout == False, f"Non-X-class flare {flare_class} should not trigger immediate blackout"


@pytest.mark.property
@given(
    ml_preds=st.dictionaries(
        keys=st.sampled_from(['metric1', 'metric2', 'metric3']),
        values=st.floats(min_value=0.0, max_value=100.0),
        min_size=1,
        max_size=3
    ),
    physics_preds=st.dictionaries(
        keys=st.sampled_from(['metric1', 'metric2', 'metric3']),
        values=st.floats(min_value=0.0, max_value=100.0),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50, deadline=None)
def test_fusion_handles_all_keys(ml_preds, physics_preds):
    """Test that fusion handles all keys from both prediction sets"""
    combiner = FusionCombiner()
    
    combined = combiner.combine_predictions(ml_preds, physics_preds)
    
    # All keys from both sets should be in combined result
    all_keys = set(ml_preds.keys()) | set(physics_preds.keys())
    
    assert set(combined.keys()) == all_keys, \
        "Combined predictions should include all keys from both sources"


@pytest.mark.property
@given(
    ml_val=st.floats(min_value=40.0, max_value=60.0),
    physics_val=st.floats(min_value=45.0, max_value=65.0)
)
@settings(max_examples=50, deadline=None)
def test_no_conflict_when_predictions_agree(ml_val, physics_val):
    """Test that no conflict is detected when predictions are similar"""
    combiner = FusionCombiner()
    
    # Ensure predictions are similar (differ by < 20)
    assume(abs(ml_val - physics_val) < 20)
    
    resolved, is_conflict = combiner.resolve_conflicts(ml_val, physics_val, 'test')
    
    # Should not be flagged as conflict
    assert is_conflict == False, "Should not detect conflict when difference < 20"
    
    # Should use weighted combination
    expected = 0.6 * ml_val + 0.4 * physics_val
    assert abs(resolved - expected) < 0.01, \
        "Should use weighted combination when no conflict"


@pytest.mark.property
def test_fusion_weights_sum_to_one():
    """Test that fusion weights are properly normalized"""
    combiner = FusionCombiner(ml_weight=0.6, physics_weight=0.4)
    
    total_weight = combiner.ml_weight + combiner.physics_weight
    
    assert abs(total_weight - 1.0) < 0.01, \
        f"Weights should sum to 1.0, got {total_weight}"


@pytest.mark.property
@given(
    space_weather=st.fixed_dictionaries({
        'bz': st.floats(min_value=-50.0, max_value=20.0),
        'solar_wind_speed': st.floats(min_value=300.0, max_value=900.0),
        'cme_speed': st.floats(min_value=0.0, max_value=2000.0),
        'kp_index': st.floats(min_value=0.0, max_value=9.0),
        'flare_class': st.sampled_from(['', 'C1.0', 'M2.0', 'X1.5'])
    })
)
@settings(max_examples=50, deadline=None)
def test_physics_predictions_in_valid_ranges(space_weather):
    """Test that physics predictions produce values in valid ranges"""
    engine = PhysicsRulesEngine()
    
    predictions = engine.predict_impacts(space_weather)
    
    # Check all predictions are in valid ranges
    assert 0.0 <= predictions['aviation_hf_blackout'] <= 100.0
    assert 0.0 <= predictions['telecom_degradation'] <= 100.0
    assert predictions['gps_drift_cm'] >= 0.0
    assert 1 <= predictions['power_grid_gic'] <= 10
    assert 1 <= predictions['satellite_drag'] <= 10


@pytest.mark.property
def test_discrepancy_log_tracking():
    """Test that discrepancy log properly tracks conflicts"""
    combiner = FusionCombiner()
    combiner.clear_discrepancy_log()
    
    # Create several conflicts
    combiner.resolve_conflicts(20.0, 80.0, 'field1', threshold=20.0)
    combiner.resolve_conflicts(30.0, 90.0, 'field2', threshold=20.0)
    combiner.resolve_conflicts(40.0, 95.0, 'field3', threshold=20.0)
    
    summary = combiner.get_discrepancy_summary()
    
    assert summary['total_discrepancies'] == 3
    assert len(summary['fields_with_conflicts']) == 3
    assert summary['average_difference'] > 0


@pytest.mark.property
@given(cme_speed=st.floats(min_value=0.0, max_value=3000.0))
@settings(max_examples=100, deadline=None)
def test_cme_impact_monotonic(cme_speed):
    """Test that CME impact increases monotonically with speed"""
    engine = PhysicsRulesEngine()
    
    impact = engine.calculate_cme_impact(cme_speed)
    
    # Impact should be non-negative
    assert impact >= 0.0, "CME impact should be non-negative"
    
    # For any speed, impact should not decrease with higher speed
    if cme_speed > 0:
        lower_impact = engine.calculate_cme_impact(cme_speed * 0.8)
        assert impact >= lower_impact, \
            "Higher CME speed should produce equal or greater impact"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
