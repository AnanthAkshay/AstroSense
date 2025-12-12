"""
Property-based tests for ML Model Training
Tests universal properties for model training and synthetic data
"""
import pytest
from hypothesis import given, strategies as st, settings
import numpy as np
import pandas as pd
from ml.synthetic_data_generator import SyntheticDataGenerator
from ml.model_trainer import ModelTrainer


# Feature: astrosense-space-weather, Property 7: Synthetic anomaly characteristics
@pytest.mark.property
@given(num_anomalies=st.integers(min_value=10, max_value=100))
@settings(max_examples=50, deadline=None)
def test_property_7_synthetic_anomaly_characteristics(num_anomalies):
    """
    Property 7: Synthetic anomaly characteristics
    For any generated synthetic anomaly, it should exhibit at least one extreme
    characteristic: CME speed above 1500 km/s, Bz below -20 nT, or Kp-index above 7
    
    Validates: Requirements 2.3
    """
    generator = SyntheticDataGenerator()
    
    # When we generate synthetic anomalies
    anomalies_df = generator.inject_synthetic_anomalies(num_anomalies)
    
    # Then each anomaly should have at least one extreme characteristic
    for idx, row in anomalies_df.iterrows():
        has_extreme_cme = row['cme_speed'] > 1500
        has_extreme_bz = row['bz_field'] < -20
        has_extreme_kp = row['kp_index'] > 7
        
        assert has_extreme_cme or has_extreme_bz or has_extreme_kp, \
            f"Anomaly {idx} must have at least one extreme characteristic: " \
            f"CME={row['cme_speed']}, Bz={row['bz_field']}, Kp={row['kp_index']}"
    
    # Verify we generated the correct number
    assert len(anomalies_df) == num_anomalies, \
        f"Should generate {num_anomalies} anomalies, got {len(anomalies_df)}"


# Feature: astrosense-space-weather, Property 6: Model serialization round-trip
@pytest.mark.property
@given(
    n_estimators=st.integers(min_value=10, max_value=50),
    max_depth=st.integers(min_value=5, max_value=15)
)
@settings(max_examples=20, deadline=None)
def test_property_6_model_serialization_roundtrip(n_estimators, max_depth):
    """
    Property 6: Model serialization round-trip
    For any trained Random Forest model, serializing then deserializing the model
    should produce identical predictions on the same input data
    
    Validates: Requirements 2.5
    """
    # Generate small training dataset
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=50,
        moderate_samples=30,
        severe_samples=20,
        anomaly_samples=10
    )
    
    X_train, X_val, X_test, y_train, y_val, y_test = generator.create_train_val_test_split(
        features, labels
    )
    
    # Train a model
    trainer = ModelTrainer()
    trainer.create_model(n_estimators=n_estimators, max_depth=max_depth)
    trainer.train(X_train, y_train)
    
    # Make predictions before saving
    predictions_before = trainer.predict(X_test)
    
    # Save model
    model_path = trainer.save_model(version="test")
    
    # Create new trainer and load model
    trainer2 = ModelTrainer()
    trainer2.load_model(model_path)
    
    # Make predictions after loading
    predictions_after = trainer2.predict(X_test)
    
    # Then predictions should be identical
    np.testing.assert_array_almost_equal(
        predictions_before,
        predictions_after,
        decimal=10,
        err_msg="Predictions should be identical after serialization round-trip"
    )
    
    # Clean up
    import os
    if os.path.exists(model_path):
        os.remove(model_path)
        # Also remove metadata file
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        if os.path.exists(metadata_path):
            os.remove(metadata_path)


# Additional property tests
@pytest.mark.property
@given(
    normal=st.integers(min_value=100, max_value=300),
    moderate=st.integers(min_value=50, max_value=200),
    severe=st.integers(min_value=30, max_value=100),
    anomaly=st.integers(min_value=10, max_value=50)
)
@settings(max_examples=30, deadline=None)
def test_dataset_generation_completeness(normal, moderate, severe, anomaly):
    """Test that generated dataset has correct total size"""
    generator = SyntheticDataGenerator()
    
    features, labels = generator.generate_training_dataset(
        normal_samples=normal,
        moderate_samples=moderate,
        severe_samples=severe,
        anomaly_samples=anomaly
    )
    
    expected_total = normal + moderate + severe + anomaly
    
    assert len(features) == expected_total, \
        f"Features should have {expected_total} samples, got {len(features)}"
    assert len(labels) == expected_total, \
        f"Labels should have {expected_total} samples, got {len(labels)}"
    assert len(features) == len(labels), \
        "Features and labels should have same length"


@pytest.mark.property
@given(num_samples=st.integers(min_value=50, max_value=500))
@settings(max_examples=50, deadline=None)
def test_normal_conditions_in_valid_ranges(num_samples):
    """Test that normal conditions stay within expected ranges"""
    generator = SyntheticDataGenerator()
    
    df = generator.generate_normal_conditions(num_samples)
    
    # Verify all values are in valid ranges
    assert (df['solar_wind_speed'] >= 250).all() and (df['solar_wind_speed'] <= 700).all()
    assert (df['bz_field'] >= -20).all() and (df['bz_field'] <= 20).all()
    assert (df['kp_index'] >= 0).all() and (df['kp_index'] <= 6).all()
    assert (df['proton_flux'] >= 1).all()
    
    # Normal conditions should have low impacts
    assert (df['aviation_impact'] < 30).all()
    assert (df['telecom_impact'] < 25).all()


@pytest.mark.property
@given(num_samples=st.integers(min_value=50, max_value=300))
@settings(max_examples=50, deadline=None)
def test_severe_storm_high_impacts(num_samples):
    """Test that severe storms generate high impact values"""
    generator = SyntheticDataGenerator()
    
    df = generator.generate_severe_storm(num_samples)
    
    # Severe storms should have high impacts
    assert (df['aviation_impact'] >= 60).all()
    assert (df['telecom_impact'] >= 50).all()
    assert (df['power_grid_risk'] >= 7).all()
    assert (df['satellite_drag_risk'] >= 7).all()
    
    # Should have strong negative Bz (clipped to -5 minimum)
    assert (df['bz_field'] <= -5).all()
    
    # Should have high Kp
    assert (df['kp_index'] >= 6).all()


@pytest.mark.property
def test_train_val_test_split_ratios():
    """Test that data split maintains correct ratios"""
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=100,
        moderate_samples=60,
        severe_samples=30,
        anomaly_samples=10
    )
    
    X_train, X_val, X_test, y_train, y_val, y_test = generator.create_train_val_test_split(
        features, labels,
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15
    )
    
    total = len(features)
    
    # Check sizes are approximately correct (within 1 sample tolerance)
    assert abs(len(X_train) - total * 0.7) <= 1
    assert abs(len(X_val) - total * 0.15) <= 1
    assert abs(len(X_test) - total * 0.15) <= 1
    
    # Check no data loss
    assert len(X_train) + len(X_val) + len(X_test) == total


@pytest.mark.property
@given(n_estimators=st.integers(min_value=10, max_value=100))
@settings(max_examples=20, deadline=None)
def test_model_training_improves_over_baseline(n_estimators):
    """Test that trained model performs better than random baseline"""
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=100,
        moderate_samples=60,
        severe_samples=40,
        anomaly_samples=20
    )
    
    X_train, X_val, X_test, y_train, y_val, y_test = generator.create_train_val_test_split(
        features, labels
    )
    
    # Train model
    trainer = ModelTrainer()
    trainer.create_model(n_estimators=n_estimators, max_depth=10)
    metrics = trainer.train(X_train, y_train, X_val, y_val)
    
    # Model should have positive R² (better than mean baseline)
    assert metrics['train_r2'] > 0, "Training R² should be positive"
    
    if 'val_r2' in metrics:
        assert metrics['val_r2'] > 0, "Validation R² should be positive"


@pytest.mark.property
def test_feature_importance_sums_to_one():
    """Test that feature importances sum to approximately 1.0"""
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=100,
        moderate_samples=60,
        severe_samples=40,
        anomaly_samples=20
    )
    
    X_train, _, _, y_train, _, _ = generator.create_train_val_test_split(features, labels)
    
    trainer = ModelTrainer()
    trainer.create_model(n_estimators=50)
    trainer.train(X_train, y_train)
    
    # Feature importances should sum to 1.0
    total_importance = sum(trainer.feature_importance.values())
    assert abs(total_importance - 1.0) < 0.01, \
        f"Feature importances should sum to 1.0, got {total_importance}"


@pytest.mark.property
def test_model_metadata_completeness():
    """Test that saved model metadata contains all required fields"""
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=50,
        moderate_samples=30,
        severe_samples=20,
        anomaly_samples=10
    )
    
    X_train, _, _, y_train, _, _ = generator.create_train_val_test_split(features, labels)
    
    trainer = ModelTrainer()
    trainer.create_model()
    trainer.train(X_train, y_train)
    
    model_path = trainer.save_model(version="test_metadata")
    
    # Check metadata completeness
    assert 'version' in trainer.model_metadata
    assert 'timestamp' in trainer.model_metadata
    assert 'model_type' in trainer.model_metadata
    assert 'feature_importance' in trainer.model_metadata
    assert 'model_file' in trainer.model_metadata
    
    # Clean up
    import os
    if os.path.exists(model_path):
        os.remove(model_path)
        metadata_path = model_path.replace('.pkl', '_metadata.json')
        if os.path.exists(metadata_path):
            os.remove(metadata_path)


@pytest.mark.property
def test_predictions_shape_matches_labels():
    """Test that predictions have same shape as labels"""
    generator = SyntheticDataGenerator()
    features, labels = generator.generate_training_dataset(
        normal_samples=50,
        moderate_samples=30,
        severe_samples=20,
        anomaly_samples=10
    )
    
    X_train, X_test, _, y_train, y_test, _ = generator.create_train_val_test_split(
        features, labels
    )
    
    trainer = ModelTrainer()
    trainer.create_model(n_estimators=20)
    trainer.train(X_train, y_train)
    
    predictions = trainer.predict(X_test)
    
    assert predictions.shape == y_test.shape, \
        f"Predictions shape {predictions.shape} should match labels shape {y_test.shape}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
