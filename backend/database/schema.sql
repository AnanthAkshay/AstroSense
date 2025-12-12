-- AstroSense Database Schema

-- Space Weather Data Table
CREATE TABLE IF NOT EXISTS space_weather_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    solar_wind_speed FLOAT,
    bz_field FLOAT,
    kp_index FLOAT,
    proton_flux FLOAT,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_timestamp_source UNIQUE (timestamp, source)
);

CREATE INDEX idx_space_weather_timestamp ON space_weather_data(timestamp DESC);
CREATE INDEX idx_space_weather_source ON space_weather_data(source);

-- CME Events Table
CREATE TABLE IF NOT EXISTS cme_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    detection_time TIMESTAMP NOT NULL,
    cme_speed FLOAT,
    predicted_arrival TIMESTAMP,
    confidence_lower TIMESTAMP,
    confidence_upper TIMESTAMP,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cme_detection_time ON cme_events(detection_time DESC);
CREATE INDEX idx_cme_predicted_arrival ON cme_events(predicted_arrival);

-- Solar Flares Table
CREATE TABLE IF NOT EXISTS solar_flares (
    id SERIAL PRIMARY KEY,
    flare_id VARCHAR(100) UNIQUE NOT NULL,
    detection_time TIMESTAMP NOT NULL,
    flare_class VARCHAR(10) NOT NULL,
    peak_time TIMESTAMP,
    location VARCHAR(100),
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flare_detection_time ON solar_flares(detection_time DESC);
CREATE INDEX idx_flare_class ON solar_flares(flare_class);

-- Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    aviation_hf_blackout_prob FLOAT,
    aviation_polar_risk FLOAT,
    telecom_signal_degradation FLOAT,
    gps_drift_cm FLOAT,
    power_grid_gic_risk INTEGER,
    satellite_drag_risk INTEGER,
    composite_score FLOAT,
    model_version VARCHAR(50) NOT NULL,
    input_features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_predictions_timestamp ON predictions(timestamp DESC);
CREATE INDEX idx_predictions_composite_score ON predictions(composite_score DESC);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(100) UNIQUE NOT NULL,
    alert_type VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_sectors TEXT[],
    mitigation_recommendations TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_archived ON alerts(archived);

-- Backtest Results Table
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    predicted_impacts JSONB,
    actual_impacts JSONB,
    accuracy_metrics JSONB,
    timeline JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtest_event_date ON backtest_results(event_date DESC);

-- Composite Score History Table (for trend analysis)
CREATE TABLE IF NOT EXISTS composite_score_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    composite_score FLOAT NOT NULL,
    aviation_contribution FLOAT,
    telecom_contribution FLOAT,
    gps_contribution FLOAT,
    power_grid_contribution FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_composite_history_timestamp ON composite_score_history(timestamp DESC);
