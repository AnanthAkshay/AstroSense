"""
Example usage of the AstroSense Database Layer
Demonstrates common operations and integration patterns
"""
from datetime import datetime, timedelta
from database import DatabaseManager
from models.space_weather import SpaceWeatherData, CMEEvent, SolarFlare
from models.prediction import SectorPredictions, CompositeScoreHistory
from models.alert import Alert, AlertType, AlertSeverity


def example_space_weather_workflow():
    """Example: Store and retrieve space weather data"""
    db = DatabaseManager()
    
    # Insert space weather measurement
    data = SpaceWeatherData(
        timestamp=datetime.utcnow(),
        solar_wind_speed=650.0,
        bz_field=-12.5,
        kp_index=6.5,
        proton_flux=250.0,
        source="NOAA_SWPC"
    )
    
    record_id = db.insert_space_weather_data(data)
    print(f"Inserted space weather data with ID: {record_id}")
    
    # Query recent data
    recent_data = db.get_space_weather_data(
        start_time=datetime.utcnow() - timedelta(hours=24),
        limit=100
    )
    print(f"Retrieved {len(recent_data)} recent measurements")
    
    db.close()


def example_prediction_workflow():
    """Example: Store predictions with model versioning"""
    db = DatabaseManager()
    
    # Create prediction
    prediction = SectorPredictions(
        timestamp=datetime.utcnow(),
        aviation_hf_blackout_prob=75.5,
        aviation_polar_risk=82.0,
        telecom_signal_degradation=45.3,
        gps_drift_cm=125.7,
        power_grid_gic_risk=8,
        satellite_drag_risk=7,
        composite_score=68.4,
        model_version="v1.2.3",
        input_features={
            'solar_wind_speed': 650.0,
            'bz_field': -12.5,
            'kp_index': 6.5,
            'proton_flux': 250.0,
            'cme_speed': 1200.0,
            'flare_class_encoded': 5
        }
    )
    
    record_id = db.insert_prediction(prediction)
    print(f"Inserted prediction with ID: {record_id}")
    
    # Store composite score history for trend analysis
    score_history = CompositeScoreHistory(
        timestamp=datetime.utcnow(),
        composite_score=68.4,
        aviation_contribution=26.4,  # 0.35 * 75.5
        telecom_contribution=11.3,   # 0.25 * 45.3
        gps_contribution=25.1,       # 0.20 * 125.7 (normalized)
        power_grid_contribution=5.6  # 0.20 * 28 (normalized)
    )
    
    history_id = db.insert_composite_score_history(score_history)
    print(f"Inserted composite score history with ID: {history_id}")
    
    db.close()


def example_alert_workflow():
    """Example: Create and manage alerts"""
    db = DatabaseManager()
    
    # Create flash alert for X-class flare
    alert = Alert(
        alert_id=f"FLASH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        alert_type=AlertType.FLASH,
        severity=AlertSeverity.CRITICAL,
        title="X5.2 Solar Flare Detected",
        description="Major X-class solar flare detected at 14:23 UTC. Immediate HF radio blackouts expected.",
        affected_sectors=["aviation", "telecom", "emergency_services"],
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=2),
        mitigation_recommendations=[
            "Switch to backup communication systems",
            "Reroute polar flights to lower latitudes",
            "Monitor power grid stability"
        ]
    )
    
    alert_id = db.insert_alert(alert)
    print(f"Inserted alert with ID: {alert_id}")
    
    # Get active alerts
    active_alerts = db.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    
    # Archive expired alerts
    archived_count = db.archive_expired_alerts()
    print(f"Archived {archived_count} expired alerts")
    
    db.close()


def example_cme_tracking():
    """Example: Track CME events and predictions"""
    db = DatabaseManager()
    
    # Insert CME event
    cme = CMEEvent(
        event_id="CME_20240515_001",
        detection_time=datetime.utcnow(),
        cme_speed=1450.0,
        predicted_arrival=datetime.utcnow() + timedelta(hours=36),
        confidence_interval=(
            datetime.utcnow() + timedelta(hours=32),
            datetime.utcnow() + timedelta(hours=40)
        ),
        source="NASA_DONKI"
    )
    
    cme_id = db.insert_cme_event(cme)
    print(f"Inserted CME event with ID: {cme_id}")
    
    # Query recent CME events
    recent_cmes = db.get_cme_events(
        start_time=datetime.utcnow() - timedelta(days=7),
        limit=50
    )
    print(f"Recent CME events: {len(recent_cmes)}")
    
    db.close()


def example_trend_analysis():
    """Example: Retrieve historical data for trend analysis"""
    db = DatabaseManager()
    
    # Get composite score history for the last 7 days
    history = db.get_composite_score_history(
        start_time=datetime.utcnow() - timedelta(days=7),
        end_time=datetime.utcnow(),
        limit=10000
    )
    
    print(f"Retrieved {len(history)} historical score records")
    
    # Analyze trends
    if history:
        scores = [record['composite_score'] for record in history]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        print(f"Average composite score: {avg_score:.2f}")
        print(f"Maximum composite score: {max_score:.2f}")
        print(f"Minimum composite score: {min_score:.2f}")
    
    db.close()


def example_automatic_archival():
    """Example: Automatic data archival"""
    db = DatabaseManager()
    
    # Check storage usage
    usage = db.check_storage_usage()
    print(f"Current storage usage: {usage:.1f}%")
    
    # Trigger automatic archival if needed
    result = db.auto_archive_if_needed()
    
    if result:
        print("Automatic archival triggered:")
        for table, count in result.items():
            print(f"  {table}: {count} records archived")
    else:
        print("No archival needed (storage below 80%)")
    
    db.close()


def example_performance_monitoring():
    """Example: Monitor database write performance"""
    import time
    
    db = DatabaseManager()
    
    # Measure write performance
    start_time = time.time()
    
    data = SpaceWeatherData(
        timestamp=datetime.utcnow(),
        solar_wind_speed=500.0,
        bz_field=-5.0,
        kp_index=4.0,
        proton_flux=100.0,
        source="PERFORMANCE_TEST"
    )
    
    record_id = db.insert_space_weather_data(data)
    
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    
    print(f"Write completed in {duration_ms:.2f}ms")
    print(f"Performance requirement: {'PASS' if duration_ms < 500 else 'FAIL'} (< 500ms)")
    
    db.close()


if __name__ == "__main__":
    print("=== AstroSense Database Layer Examples ===\n")
    
    try:
        print("1. Space Weather Data Workflow")
        example_space_weather_workflow()
        print()
        
        print("2. Prediction Workflow")
        example_prediction_workflow()
        print()
        
        print("3. Alert Workflow")
        example_alert_workflow()
        print()
        
        print("4. CME Tracking")
        example_cme_tracking()
        print()
        
        print("5. Trend Analysis")
        example_trend_analysis()
        print()
        
        print("6. Automatic Archival")
        example_automatic_archival()
        print()
        
        print("7. Performance Monitoring")
        example_performance_monitoring()
        print()
        
        print("=== All examples completed successfully ===")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Ensure DATABASE_URL is set and PostgreSQL is running")
        print("See backend/tests/README_DATABASE_TESTS.md for setup instructions")
