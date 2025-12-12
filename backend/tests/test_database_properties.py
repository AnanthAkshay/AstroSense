"""
Property-based tests for Database Manager
Tests universal properties that should hold for all database operations

Feature: astrosense-space-weather
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import time
import os
from typing import Dict, Any

from database.manager import DatabaseManager
from models.space_weather import SpaceWeatherData, CMEEvent, SolarFlare
from models.prediction import SectorPredictions, CompositeScoreHistory, BacktestResult
from models.alert import Alert, AlertType, AlertSeverity


# ==================== Test Fixtures ====================

@pytest.fixture(scope="module")
def db_manager():
    """Create a database manager for testing"""
    # Use test database URL if available, otherwise skip tests
    test_db_url = os.getenv('TEST_DATABASE_URL')
    if not test_db_url:
        pytest.skip("TEST_DATABASE_URL not set - skipping database tests")
    
    manager = DatabaseManager(database_url=test_db_url, pool_size=5, max_overflow=10)
    yield manager
    manager.close()


@pytest.fixture(autouse=True)
def cleanup_test_data(db_manager):
    """Clean up test data after each test"""
    yield
    # Clean up tables after test
    with db_manager.get_cursor() as cursor:
        cursor.execute("DELETE FROM space_weather_data WHERE source LIKE 'TEST_%'")
        cursor.execute("DELETE FROM cme_events WHERE source LIKE 'TEST_%'")
        cursor.execute("DELETE FROM solar_flares WHERE source LIKE 'TEST_%'")
        cursor.execute("DELETE FROM predictions WHERE model_version LIKE 'TEST_%'")
        cursor.execute("DELETE FROM alerts WHERE alert_id LIKE 'TEST_%'")
        cursor.execute("DELETE FROM composite_score_history WHERE timestamp > NOW() - INTERVAL '1 hour'")
        cursor.execute("DELETE FROM backtest_results WHERE event_name LIKE 'TEST_%'")


# ==================== Custom Strategies ====================

@st.composite
def space_weather_data_strategy(draw):
    """Generate valid SpaceWeatherData objects"""
    timestamp = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2025, 12, 31)
    ))
    
    return SpaceWeatherData(
        timestamp=timestamp,
        solar_wind_speed=draw(st.one_of(st.none(), st.floats(min_value=200, max_value=1500))),
        bz_field=draw(st.one_of(st.none(), st.floats(min_value=-50, max_value=50))),
        kp_index=draw(st.one_of(st.none(), st.floats(min_value=0, max_value=9))),
        proton_flux=draw(st.one_of(st.none(), st.floats(min_value=0, max_value=10000))),
        source=f"TEST_{draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))}"
    )


@st.composite
def cme_event_strategy(draw):
    """Generate valid CMEEvent objects"""
    detection_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2025, 12, 31)
    ))
    
    predicted_arrival = draw(st.one_of(
        st.none(),
        st.datetimes(
            min_value=detection_time,
            max_value=detection_time + timedelta(days=5)
        )
    ))
    
    if predicted_arrival:
        confidence_interval = (
            predicted_arrival - timedelta(hours=draw(st.integers(min_value=1, max_value=12))),
            predicted_arrival + timedelta(hours=draw(st.integers(min_value=1, max_value=12)))
        )
    else:
        confidence_interval = None
    
    return CMEEvent(
        event_id=f"TEST_CME_{draw(st.integers(min_value=1000, max_value=9999))}",
        detection_time=detection_time,
        cme_speed=draw(st.one_of(st.none(), st.floats(min_value=200, max_value=3000))),
        predicted_arrival=predicted_arrival,
        confidence_interval=confidence_interval,
        source=f"TEST_{draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))}"
    )


@st.composite
def solar_flare_strategy(draw):
    """Generate valid SolarFlare objects"""
    detection_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2025, 12, 31)
    ))
    
    peak_time = draw(st.one_of(
        st.none(),
        st.datetimes(
            min_value=detection_time,
            max_value=detection_time + timedelta(hours=2)
        )
    ))
    
    return SolarFlare(
        flare_id=f"TEST_FLARE_{draw(st.integers(min_value=1000, max_value=9999))}",
        detection_time=detection_time,
        flare_class=draw(st.sampled_from(['X', 'M', 'C', 'B', 'A'])),
        peak_time=peak_time,
        location=draw(st.one_of(st.none(), st.text(min_size=5, max_size=20))),
        source=f"TEST_{draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))}"
    )


@st.composite
def sector_predictions_strategy(draw):
    """Generate valid SectorPredictions objects"""
    return SectorPredictions(
        timestamp=draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )),
        aviation_hf_blackout_prob=draw(st.floats(min_value=0, max_value=100)),
        aviation_polar_risk=draw(st.floats(min_value=0, max_value=100)),
        telecom_signal_degradation=draw(st.floats(min_value=0, max_value=100)),
        gps_drift_cm=draw(st.floats(min_value=0, max_value=500)),
        power_grid_gic_risk=draw(st.integers(min_value=1, max_value=10)),
        satellite_drag_risk=draw(st.integers(min_value=1, max_value=10)),
        composite_score=draw(st.floats(min_value=0, max_value=100)),
        model_version=f"TEST_v{draw(st.integers(min_value=1, max_value=100))}",
        input_features={
            'solar_wind_speed': draw(st.floats(min_value=200, max_value=1500)),
            'bz_field': draw(st.floats(min_value=-50, max_value=50)),
            'kp_index': draw(st.floats(min_value=0, max_value=9))
        }
    )


@st.composite
def composite_score_history_strategy(draw):
    """Generate valid CompositeScoreHistory objects"""
    aviation = draw(st.floats(min_value=0, max_value=35))
    telecom = draw(st.floats(min_value=0, max_value=25))
    gps = draw(st.floats(min_value=0, max_value=20))
    power_grid = draw(st.floats(min_value=0, max_value=20))
    
    return CompositeScoreHistory(
        timestamp=draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )),
        composite_score=aviation + telecom + gps + power_grid,
        aviation_contribution=aviation,
        telecom_contribution=telecom,
        gps_contribution=gps,
        power_grid_contribution=power_grid
    )


# ==================== Property Tests ====================

@settings(max_examples=100, deadline=5000)
@given(data=space_weather_data_strategy())
def test_property_47_data_persistence_with_metadata(db_manager, data):
    """
    Feature: astrosense-space-weather, Property 47: Data persistence with metadata
    
    For any received space weather data, the database record should include 
    the data values, timestamp, and source identifier
    
    Validates: Requirements 14.1
    """
    # Insert data
    record_id = db_manager.insert_space_weather_data(data)
    
    # Verify record was created
    assert record_id is not None
    assert record_id > 0
    
    # Retrieve the data
    retrieved = db_manager.get_space_weather_data(
        start_time=data.timestamp - timedelta(seconds=1),
        end_time=data.timestamp + timedelta(seconds=1),
        source=data.source,
        limit=1
    )
    
    # Verify data persistence with metadata
    assert len(retrieved) > 0
    record = retrieved[0]
    
    # Check all required fields are present
    assert 'timestamp' in record
    assert 'source' in record
    assert 'solar_wind_speed' in record
    assert 'bz_field' in record
    assert 'kp_index' in record
    assert 'proton_flux' in record
    
    # Verify values match
    assert record['source'] == data.source
    # Timestamp comparison (allowing for microsecond differences)
    assert abs((record['timestamp'] - data.timestamp).total_seconds()) < 1


@settings(max_examples=100, deadline=5000)
@given(prediction=sector_predictions_strategy())
def test_property_48_prediction_storage_with_versioning(db_manager, prediction):
    """
    Feature: astrosense-space-weather, Property 48: Prediction storage with versioning
    
    For any generated prediction, the database record should include 
    the prediction values, model version, and input feature vector
    
    Validates: Requirements 14.2
    """
    # Insert prediction
    record_id = db_manager.insert_prediction(prediction)
    
    # Verify record was created
    assert record_id is not None
    assert record_id > 0
    
    # Retrieve the prediction
    retrieved = db_manager.get_predictions(
        start_time=prediction.timestamp - timedelta(seconds=1),
        end_time=prediction.timestamp + timedelta(seconds=1),
        limit=1
    )
    
    # Verify prediction storage with versioning
    assert len(retrieved) > 0
    record = retrieved[0]
    
    # Check all required fields are present
    assert 'timestamp' in record
    assert 'model_version' in record
    assert 'input_features' in record
    assert 'aviation_hf_blackout_prob' in record
    assert 'telecom_signal_degradation' in record
    assert 'gps_drift_cm' in record
    assert 'power_grid_gic_risk' in record
    assert 'satellite_drag_risk' in record
    assert 'composite_score' in record
    
    # Verify model version is stored
    assert record['model_version'] == prediction.model_version
    
    # Verify input features are stored
    assert record['input_features'] is not None
    assert isinstance(record['input_features'], dict)


@settings(max_examples=50, deadline=5000)
@given(prediction=sector_predictions_strategy())
def test_property_49_database_write_performance(db_manager, prediction):
    """
    Feature: astrosense-space-weather, Property 49: Database write performance
    
    For any database write transaction, it should complete within 500 milliseconds
    
    Validates: Requirements 14.3
    """
    # Measure write time
    start_time = time.time()
    record_id = db_manager.insert_prediction(prediction)
    end_time = time.time()
    
    write_duration_ms = (end_time - start_time) * 1000
    
    # Verify write completed successfully
    assert record_id is not None
    assert record_id > 0
    
    # Verify write performance (500ms requirement)
    assert write_duration_ms < 500, f"Write took {write_duration_ms:.2f}ms, exceeds 500ms limit"


@settings(max_examples=20, deadline=10000)
def test_property_50_automatic_data_archival(db_manager):
    """
    Feature: astrosense-space-weather, Property 50: Automatic data archival
    
    For any database state where storage exceeds 80 percent capacity, 
    the system should archive data older than 1 year to cold storage
    
    Validates: Requirements 14.5
    """
    # Insert old test data (older than 1 year)
    old_timestamp = datetime.utcnow() - timedelta(days=400)
    old_data = SpaceWeatherData(
        timestamp=old_timestamp,
        solar_wind_speed=500.0,
        bz_field=-10.0,
        kp_index=5.0,
        proton_flux=100.0,
        source="TEST_OLD_DATA"
    )
    
    record_id = db_manager.insert_space_weather_data(old_data)
    assert record_id > 0
    
    # Verify data exists
    retrieved_before = db_manager.get_space_weather_data(
        start_time=old_timestamp - timedelta(days=1),
        end_time=old_timestamp + timedelta(days=1),
        source="TEST_OLD_DATA"
    )
    assert len(retrieved_before) > 0
    
    # Trigger archival for data older than 1 year
    cutoff_date = datetime.utcnow() - timedelta(days=365)
    archived_counts = db_manager.archive_old_data(cutoff_date=cutoff_date)
    
    # Verify archival occurred
    assert isinstance(archived_counts, dict)
    assert 'space_weather_data' in archived_counts
    assert archived_counts['space_weather_data'] > 0
    
    # Verify old data was removed
    retrieved_after = db_manager.get_space_weather_data(
        start_time=old_timestamp - timedelta(days=1),
        end_time=old_timestamp + timedelta(days=1),
        source="TEST_OLD_DATA"
    )
    assert len(retrieved_after) == 0


@settings(max_examples=100, deadline=5000)
@given(score_data=composite_score_history_strategy())
def test_property_72_historical_composite_score_retrieval(db_manager, score_data):
    """
    Feature: astrosense-space-weather, Property 72: Historical composite score retrieval
    
    For any query for historical composite scores, the system should return 
    time-series data suitable for trend analysis
    
    Validates: Requirements 19.5
    """
    # Insert composite score history
    record_id = db_manager.insert_composite_score_history(score_data)
    
    # Verify record was created
    assert record_id is not None
    assert record_id > 0
    
    # Retrieve historical scores
    retrieved = db_manager.get_composite_score_history(
        start_time=score_data.timestamp - timedelta(seconds=1),
        end_time=score_data.timestamp + timedelta(seconds=1)
    )
    
    # Verify time-series data is returned
    assert len(retrieved) > 0
    record = retrieved[0]
    
    # Check all required fields for trend analysis are present
    assert 'timestamp' in record
    assert 'composite_score' in record
    assert 'aviation_contribution' in record
    assert 'telecom_contribution' in record
    assert 'gps_contribution' in record
    assert 'power_grid_contribution' in record
    
    # Verify data is suitable for trend analysis (ordered by time)
    if len(retrieved) > 1:
        for i in range(len(retrieved) - 1):
            # Should be in ascending time order
            assert retrieved[i]['timestamp'] <= retrieved[i + 1]['timestamp']
    
    # Verify values match
    assert abs(record['composite_score'] - score_data.composite_score) < 0.01
    assert abs(record['aviation_contribution'] - score_data.aviation_contribution) < 0.01


# ==================== Additional Integration Tests ====================

def test_cme_event_crud_operations(db_manager):
    """Test CME event CRUD operations"""
    # Create
    event = CMEEvent(
        event_id="TEST_CME_CRUD_001",
        detection_time=datetime.utcnow(),
        cme_speed=1200.0,
        predicted_arrival=datetime.utcnow() + timedelta(days=2),
        confidence_interval=(
            datetime.utcnow() + timedelta(days=1, hours=20),
            datetime.utcnow() + timedelta(days=2, hours=4)
        ),
        source="TEST_CRUD"
    )
    
    record_id = db_manager.insert_cme_event(event)
    assert record_id > 0
    
    # Read
    retrieved = db_manager.get_cme_events(
        start_time=event.detection_time - timedelta(seconds=1),
        end_time=event.detection_time + timedelta(seconds=1)
    )
    
    assert len(retrieved) > 0
    assert retrieved[0]['event_id'] == event.event_id
    assert retrieved[0]['cme_speed'] == event.cme_speed


def test_solar_flare_crud_operations(db_manager):
    """Test solar flare CRUD operations"""
    # Create
    flare = SolarFlare(
        flare_id="TEST_FLARE_CRUD_001",
        detection_time=datetime.utcnow(),
        flare_class="X",
        peak_time=datetime.utcnow() + timedelta(minutes=15),
        location="N15W30",
        source="TEST_CRUD"
    )
    
    record_id = db_manager.insert_solar_flare(flare)
    assert record_id > 0
    
    # Read
    retrieved = db_manager.get_solar_flares(
        start_time=flare.detection_time - timedelta(seconds=1),
        end_time=flare.detection_time + timedelta(seconds=1)
    )
    
    assert len(retrieved) > 0
    assert retrieved[0]['flare_id'] == flare.flare_id
    assert retrieved[0]['flare_class'] == flare.flare_class


def test_alert_lifecycle(db_manager):
    """Test alert creation and archival"""
    # Create alert
    alert = Alert(
        alert_id="TEST_ALERT_001",
        alert_type=AlertType.FLASH,
        severity=AlertSeverity.HIGH,
        title="Test Flash Alert",
        description="Test alert for database operations",
        affected_sectors=["aviation", "telecom"],
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() - timedelta(hours=3),  # Already expired
        mitigation_recommendations=["Monitor conditions", "Prepare backup systems"]
    )
    
    record_id = db_manager.insert_alert(alert)
    assert record_id > 0
    
    # Archive expired alerts
    archived_count = db_manager.archive_expired_alerts()
    assert archived_count > 0
