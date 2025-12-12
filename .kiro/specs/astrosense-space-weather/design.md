# AstroSense Design Document

## Overview

AstroSense is a real-time space weather intelligence system that combines machine learning predictions with physics-based rules to forecast infrastructure impacts from solar events. The system architecture follows a layered approach with clear separation between data ingestion, processing, prediction, and presentation layers.

The system processes data from NASA DONKI and NOAA SWPC APIs, applies a hybrid ML + Physics Fusion Engine, and delivers predictions through a responsive web dashboard with real-time updates. The architecture supports three operational modes: live monitoring, flash alerting, and historical backtesting.

## Architecture

### System Architecture

The system follows a layered architecture with seven distinct layers:

1. **External Data Sources Layer**: NASA DONKI API and NOAA SWPC API
2. **Data Ingestion Layer**: API Client Manager with rate limiting and retry logic
3. **Data Processing Layer**: Validation, normalization, and feature extraction
4. **ML + Physics Fusion Engine**: Combined ML predictions and physics rules
5. **Impact Translation Layer**: Sector-specific predictors and composite scoring
6. **Alert & Storage Layer**: Alert management and PostgreSQL database
7. **API & Streaming Layer**: FastAPI with REST and WebSocket endpoints
8. **Presentation Layer**: React + Next.js dashboard with visualizations

### Data Flow

The system processes data through the following pipeline:

1. Fetch data from NASA DONKI and NOAA SWPC APIs
2. Validate data completeness and correctness
3. Normalize numerical features and extract feature vectors
4. Generate ML predictions using Random Forest (60% weight)
5. Apply physics rules including McPherron relation (40% weight)
6. Combine predictions using weighted fusion
7. Translate to sector-specific impacts (aviation, telecom, GPS, power, satellite)
8. Calculate composite impact score
9. Generate alerts if thresholds are exceeded
10. Store predictions and data to database
11. Stream updates to dashboard via WebSocket
12. Display on user interface

## Components and Interfaces

### 1. Data Ingestion Layer

**API Client Manager**
- Manages connections to external APIs with reliability features
- Executes HTTP requests to NASA DONKI and NOAA SWPC
- Implements exponential backoff retry logic (max 3 retries)
- Caches responses for 60 seconds to respect rate limits
- Parses JSON responses and handles errors gracefully

### 2. Data Processing Layer

**Validation Engine**
- Ensures data quality and completeness
- Verifies all required fields are present
- Checks numerical values are within plausible ranges
- Validates timestamp chronology
- Logs validation failures

**Normalization Engine**
- Standardizes data for ML model consumption
- Normalizes numerical features to [0, 1] range
- Encodes categorical features (flare classes)
- Imputes missing values using 6-hour median
- Preserves raw values for audit

**Feature Extraction Engine**
- Transforms raw data into ML-ready feature vectors
- Extracts 12-dimensional feature vectors
- Computes derived features (e.g., Bz rate of change)
- Handles temporal aggregations

### 3. ML + Physics Fusion Engine

**ML Predictor**
- Generates predictions using trained Random Forest model
- Loads trained model from disk
- Executes predictions on feature vectors
- Returns sector-specific risk scores
- Weights predictions at 60%

**Physics Rules Engine**
- Applies scientific rules for space weather impacts
- Implements McPherron relation (Bz + wind speed)
- Applies CME speed impact rules
- Triggers immediate alerts for X-class flares
- Weights rules at 40%

**Fusion Combiner**
- Merges ML and physics predictions
- Combines predictions with 60/40 weighting
- Resolves conflicts using conservative estimates
- Logs discrepancies for analysis

### 4. Impact Translation Layer

**Sector Predictors**
- Aviation: Calculates HF blackout probability and polar route risk
- Telecom: Computes signal degradation percentage
- GPS: Estimates positional drift in centimeters
- Power Grid: Assesses GIC risk level (1-10)
- Satellite: Determines orbital drag risk (1-10)

**Composite Score Calculator**
- Computes overall system risk score
- Applies weighted formula: 0.35×Aviation + 0.25×Telecom + 0.20×GPS + 0.20×PowerGrid
- Scales to 0-100 range
- Classifies severity (low/moderate/high)

### 5. Alert & Storage Layer

**Alert Manager**
- Creates flash alerts for X-class flares (< 10 seconds)
- Generates impact forecasts for CMEs (24-48 hours ahead)
- Prioritizes alerts by severity
- Expires alerts after 2 hours

**Database Manager**
- Stores historical space weather data
- Saves prediction snapshots with metadata
- Archives old data (> 1 year) to cold storage
- Executes indexed queries efficiently

### 6. API & Streaming Layer

**FastAPI Backend**
- POST /api/predict-impact: Returns sector-specific predictions
- GET /api/fetch-data: Returns current space weather data
- POST /api/backtest: Initiates historical replay
- WS /api/stream: WebSocket for real-time updates

### 7. Presentation Layer

**React Dashboard Components**
- HeatmapComponent: 3D Earth globe using Cesium.js with geomagnetic shading
- ChartsComponent: Time-series graphs using Highcharts.js
- AlertsComponent: Flash alerts and impact forecasts panel
- RiskCardsComponent: Sector-specific risk display cards
- ImpactTableComponent: Tabular view of predicted impacts
- BacktestComponent: Historical event replay controls

## Data Models

### SpaceWeatherData
- timestamp: datetime
- solar_wind_speed: float (km/s)
- bz_field: float (nT)
- kp_index: float (0-9)
- proton_flux: float (particles/cm²/s/sr)
- source: string

### CMEEvent
- event_id: string
- detection_time: datetime
- cme_speed: float (km/s)
- predicted_arrival: datetime
- confidence_interval: tuple of datetimes
- source: string

### SolarFlare
- flare_id: string
- detection_time: datetime
- flare_class: string (X, M, C, B, A)
- peak_time: datetime
- location: string
- source: string

### FeatureVector
- solar_wind_speed_norm: float
- bz_field_norm: float
- kp_index_norm: float
- proton_flux_norm: float
- cme_speed_norm: float
- flare_class_encoded: int
- bz_rate_of_change: float
- wind_speed_variance: float
- time_since_last_flare: float
- cme_arrival_proximity: float
- geomagnetic_latitude: float
- local_time_factor: float

### SectorPredictions
- aviation_hf_blackout_prob: float (0-100%)
- aviation_polar_risk: float (0-100)
- telecom_signal_degradation: float (0-100%)
- gps_drift_cm: float (centimeters)
- power_grid_gic_risk: int (1-10)
- satellite_drag_risk: int (1-10)
- composite_score: float (0-100)
- timestamp: datetime
- model_version: string

### Alert
- alert_id: string
- alert_type: string (FLASH or FORECAST)
- severity: string (LOW, MODERATE, HIGH, CRITICAL)
- title: string
- description: string
- affected_sectors: list of strings
- created_at: datetime
- expires_at: datetime
- mitigation_recommendations: list of strings

### BacktestResult
- event_name: string
- event_date: datetime
- predicted_impacts: SectorPredictions
- actual_impacts: SectorPredictions
- accuracy_metrics: dictionary
- timeline: list of tuples

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Data Ingestion Properties

Property 1: API data parsing completeness
*For any* valid NASA DONKI API response, the system should extract all required fields including CME events, solar flare classifications, and arrival time predictions
**Validates: Requirements 1.1**

Property 2: NOAA SWPC data extraction
*For any* valid NOAA SWPC JSON feed response, the system should extract solar wind speed, Bz magnetic field direction, Kp-index, and proton flux measurements
**Validates: Requirements 1.2**

Property 3: Retry with exponential backoff
*For any* failed API request, the system should retry with exponentially increasing delays and log each failure attempt
**Validates: Requirements 1.3**

Property 4: Response caching consistency
*For any* API endpoint, requests made within 60 seconds should return the cached response without making a new external API call
**Validates: Requirements 1.5**

### Machine Learning Properties

Property 5: Feature extraction completeness
*For any* raw training data, the feature extraction process should produce vectors containing all six required features: solar wind speed, Bz magnetic field, solar flare class, proton flux, CME speed, and Kp-index
**Validates: Requirements 2.1**

Property 6: Model serialization round-trip
*For any* trained Random Forest model, serializing then deserializing the model should produce identical predictions on the same input data
**Validates: Requirements 2.5**

Property 7: Synthetic anomaly characteristics
*For any* generated synthetic anomaly, it should exhibit at least one extreme characteristic: CME speed above 1500 km/s, Bz below -20 nT, or Kp-index above 7
**Validates: Requirements 2.3**

### Physics Fusion Properties

Property 8: McPherron relation application
*For any* input where Bz is below -10 nT AND solar wind speed exceeds 500 km/s, the Physics Fusion Engine should increase the storm risk prediction compared to baseline
**Validates: Requirements 3.1**

Property 9: High-speed CME impact amplification
*For any* CME with speed exceeding 1000 km/s, the predicted impact severity should be higher than for a CME with speed below 500 km/s, all other factors being equal
**Validates: Requirements 3.2**

Property 10: Fusion weighting formula
*For any* ML prediction and physics rule output, the combined fusion score should equal 0.6 times ML prediction plus 0.4 times physics prediction
**Validates: Requirements 3.4**

Property 11: Conservative conflict resolution
*For any* pair of contradictory ML and physics predictions, the system should select the higher risk estimate and log the discrepancy
**Validates: Requirements 3.5**

### Sector Prediction Properties

Property 12: Aviation risk output range
*For any* solar flare data input, the calculated aviation HF blackout probability should be a value between 0 and 100 inclusive
**Validates: Requirements 4.1**

Property 13: Polar route risk sensitivity
*For any* two inputs differing only in geomagnetic latitude or Kp-index, changing these values should affect the polar route risk calculation
**Validates: Requirements 4.2**

Property 14: Aviation alert threshold
*For any* prediction where aviation risk exceeds 70 percent, the system should generate a high-priority alert containing mitigation recommendations
**Validates: Requirements 4.3**

Property 15: Telecom degradation output range
*For any* space weather data input, the predicted telecommunications signal degradation should be a percentage between 0 and 100 inclusive
**Validates: Requirements 5.1**

Property 16: Telecom moderate threshold
*For any* prediction where signal degradation exceeds 30 percent but is below 60 percent, the system should classify the impact as moderate and issue a warning alert
**Validates: Requirements 5.2**

Property 17: Telecom critical threshold
*For any* prediction where signal degradation exceeds 60 percent, the system should classify the impact as severe and issue a critical alert
**Validates: Requirements 5.3**

Property 18: GPS drift output units
*For any* ionospheric disturbance prediction, the GPS positional drift should be expressed in centimeters as a non-negative number
**Validates: Requirements 6.1**

Property 19: GPS moderate warning threshold
*For any* prediction where GPS drift exceeds 50 centimeters but is below 200 centimeters, the system should issue a moderate accuracy warning
**Validates: Requirements 6.2**

Property 20: GPS critical warning threshold
*For any* prediction where GPS drift exceeds 200 centimeters, the system should issue a critical accuracy warning
**Validates: Requirements 6.3**

Property 21: GIC risk output range
*For any* geomagnetic storm conditions, the calculated GIC risk level should be an integer between 1 and 10 inclusive
**Validates: Requirements 7.1**

Property 22: GIC high-risk alert threshold
*For any* prediction where GIC risk exceeds level 7, the system should issue a high-risk alert with transformer protection recommendations
**Validates: Requirements 7.2**

Property 23: GIC calculation inputs
*For any* two inputs differing only in ground conductivity or grid topology factors, the GIC risk calculation should produce different results
**Validates: Requirements 7.4**

Property 24: Satellite drag risk output range
*For any* atmospheric density change prediction, the calculated satellite orbital drag risk should be an integer between 1 and 10 inclusive
**Validates: Requirements 8.1**

Property 25: Satellite drag alert threshold
*For any* prediction where orbital drag risk exceeds level 6, the system should issue an alert recommending orbit adjustment maneuvers
**Validates: Requirements 8.2**

Property 26: Multi-satellite alert prioritization
*For any* set of multiple satellite predictions, alerts should be ordered by a combination of orbital altitude and mission criticality
**Validates: Requirements 8.5**

### Visualization Properties

Property 27: Risk severity color mapping
*For any* calculated impact severity level, the heatmap should apply consistent color coding where low risk maps to green, moderate to yellow, and high risk to red
**Validates: Requirements 9.2**

Property 28: Region selection detail display
*For any* geographic region selected on the heatmap, the system should display detailed impact metrics specific to that location
**Validates: Requirements 9.4**

Property 29: Heatmap update performance
*For any* new data update, the heatmap visualization should refresh within 2 seconds without requiring a page reload
**Validates: Requirements 9.5**

Property 30: Solar wind chart units
*For any* solar wind data received, the time-series chart should plot wind speed values in kilometers per second
**Validates: Requirements 10.1**

Property 31: Bz chart units
*For any* Bz magnetic field data received, the time-series chart should plot Bz values in nanoteslas
**Validates: Requirements 10.2**

Property 32: Chart time window and resolution
*For any* displayed chart, it should show the most recent 24 hours of data with data points at 5-minute intervals
**Validates: Requirements 10.3**

Property 33: Threshold visualization
*For any* data point that crosses a critical threshold, the chart should highlight the threshold line and add an annotation marking the event
**Validates: Requirements 10.4**

### Alert Properties

Property 34: Flash alert generation speed
*For any* detected X-class solar flare, the system should generate a flash alert within 10 seconds of detection
**Validates: Requirements 11.1**

Property 35: Flash alert content completeness
*For any* generated flash alert, it should include flare classification, detection time, and a list of affected sectors
**Validates: Requirements 11.3**

Property 36: Alert prioritization and ordering
*For any* set of multiple flash alerts, they should be sorted first by severity level then by chronological order
**Validates: Requirements 11.4**

Property 37: Alert expiration lifecycle
*For any* flash alert created, it should be moved to the alert history section exactly 2 hours after creation
**Validates: Requirements 11.5**

Property 38: CME forecast confidence interval
*For any* detected CME, the Earth arrival time prediction should include a confidence interval with both lower and upper bounds
**Validates: Requirements 12.1**

Property 39: Impact forecast content completeness
*For any* generated impact forecast, it should include predicted Kp-index, sector-specific impact predictions, and mitigation recommendations
**Validates: Requirements 12.2**

Property 40: Forecast countdown display
*For any* active impact forecast, the dashboard should display a countdown timer showing time remaining until predicted CME arrival
**Validates: Requirements 12.3**

Property 41: Low confidence uncertainty indication
*For any* forecast with confidence below 70 percent, the system should display the uncertainty level and provide range estimates
**Validates: Requirements 12.4**

Property 42: Post-event accuracy logging
*For any* forecasted CME that arrives, the system should compare actual impacts to predictions and log accuracy metrics to the database
**Validates: Requirements 12.5**

### Backtesting Properties

Property 43: Backtesting chronological replay
*For any* historical event in backtesting mode, events should be replayed in chronological order based on their original timestamps
**Validates: Requirements 13.2**

Property 44: Backtesting prediction and actual display
*For any* backtesting session, the dashboard should display both predicted impacts and actual observed impacts side by side
**Validates: Requirements 13.3**

Property 45: Backtesting accuracy report generation
*For any* completed backtesting session, the system should generate an accuracy report comparing predictions to ground truth data
**Validates: Requirements 13.4**

Property 46: Backtesting mode exit without reload
*For any* active backtesting session, exiting to live data mode should transition without requiring a page reload
**Validates: Requirements 13.5**

### Data Storage Properties

Property 47: Data persistence with metadata
*For any* received space weather data, the database record should include the data values, timestamp, and source identifier
**Validates: Requirements 14.1**

Property 48: Prediction storage with versioning
*For any* generated prediction, the database record should include the prediction values, model version, and input feature vector
**Validates: Requirements 14.2**

Property 49: Database write performance
*For any* database write transaction, it should complete within 500 milliseconds
**Validates: Requirements 14.3**

Property 50: Automatic data archival
*For any* database state where storage exceeds 80 percent capacity, the system should archive data older than 1 year to cold storage
**Validates: Requirements 14.5**

### API Properties

Property 51: Predict-impact endpoint response format
*For any* valid request to the predict-impact endpoint, the response should be valid JSON containing sector-specific risk predictions
**Validates: Requirements 15.1**

Property 52: Fetch-data endpoint response format
*For any* valid request to the fetch-data endpoint, the response should be valid JSON containing current space weather measurements
**Validates: Requirements 15.2**

Property 53: Backtest endpoint response format
*For any* valid request to the backtest endpoint, the response should be valid JSON containing historical event replay data
**Validates: Requirements 15.3**

Property 54: Rate limit HTTP response
*For any* API request that exceeds rate limits, the response should have HTTP status 429 and include a retry-after header
**Validates: Requirements 15.4**

Property 55: CORS header inclusion
*For any* API response, it should include CORS headers allowing cross-origin requests
**Validates: Requirements 15.5**

### UI Responsiveness Properties

Property 56: Animation timing constraints
*For any* UI animation, the transition duration should be between 200 and 400 milliseconds
**Validates: Requirements 16.4**

Property 57: Mobile responsive layout
*For any* screen width smaller than 768 pixels, the dashboard should adapt the layout to a mobile-friendly configuration
**Validates: Requirements 16.5**

### Streaming Properties

Property 58: Real-time data push
*For any* new space weather data arrival, the system should push updates to all connected clients via WebSocket
**Validates: Requirements 17.1**

Property 59: Connection establishment performance
*For any* client connecting to the streaming endpoint, a persistent connection should be established within 2 seconds
**Validates: Requirements 17.2**

Property 60: Update frequency constraint
*For any* streaming connection, updates should be sent at intervals no longer than 10 seconds
**Validates: Requirements 17.3**

Property 61: Automatic reconnection with backoff
*For any* lost streaming connection, the client should attempt automatic reconnection with exponentially increasing delays
**Validates: Requirements 17.4**

Property 62: Broadcast to multiple clients
*For any* update event, the system should broadcast the update to all connected clients simultaneously
**Validates: Requirements 17.5**

### Feature Engineering Properties

Property 63: Normalization output range
*For any* raw numerical feature value, the normalized output should be a value between 0 and 1 inclusive
**Validates: Requirements 18.1**

Property 64: Flare class encoding
*For any* solar flare class string (X, M, C, B, A), the encoding process should produce a unique numerical value
**Validates: Requirements 18.2**

Property 65: Missing value imputation
*For any* missing data point, the imputed value should be the median of the previous 6 hours of data
**Validates: Requirements 18.3**

Property 66: Feature vector dimensionality
*For any* completed feature extraction, the output feature vector should have exactly 12 dimensions
**Validates: Requirements 18.4**

Property 67: Raw value preservation
*For any* normalized feature, the system should retain the original raw value in storage for audit purposes
**Validates: Requirements 18.5**

### Composite Scoring Properties

Property 68: Composite score calculation formula
*For any* set of sector-specific risks, the composite impact score should equal 0.35 times aviation risk plus 0.25 times telecom risk plus 0.20 times GPS drift score plus 0.20 times power grid risk
**Validates: Requirements 19.1**

Property 69: Composite score output range
*For any* calculated composite score, it should be a value between 0 and 100 inclusive with color-coded severity indication
**Validates: Requirements 19.2**

Property 70: High composite score alert
*For any* composite score exceeding 70, the system should classify overall risk as high and issue a system-wide alert
**Validates: Requirements 19.3**

Property 71: Composite score change logging
*For any* change in composite score, the system should log the change with timestamp and contributing sector factors
**Validates: Requirements 19.4**

Property 72: Historical composite score retrieval
*For any* query for historical composite scores, the system should return time-series data suitable for trend analysis
**Validates: Requirements 19.5**

### Data Validation Properties

Property 73: Required field validation
*For any* data received from external APIs, the validation engine should verify that all required fields are present
**Validates: Requirements 20.1**

Property 74: Numerical range validation
*For any* numerical value in received data, the validation engine should reject values outside physically plausible ranges
**Validates: Requirements 20.2**

Property 75: Validation failure logging
*For any* data validation failure, the system should log the error with details and skip the invalid record
**Validates: Requirements 20.3**

Property 76: Timestamp chronology validation
*For any* sequence of data records, the validation engine should verify that timestamps are in chronological order
**Validates: Requirements 20.4**

Property 77: Data quality alerting
*For any* time period where data completeness falls below 90 percent, the system should track the quality metric and generate an alert
**Validates: Requirements 20.5**

## Error Handling

The system implements comprehensive error handling across all layers:

### API Layer Errors
- Network timeouts: Retry with exponential backoff (max 3 attempts)
- Invalid responses: Log error and skip processing
- Rate limiting: Cache responses and respect retry-after headers
- Authentication failures: Alert administrators and halt requests

### Data Processing Errors
- Missing fields: Impute using historical median or skip record
- Out-of-range values: Log validation failure and reject record
- Malformed data: Parse with error recovery or discard
- Timestamp inconsistencies: Sort and validate chronology

### ML Model Errors
- Model loading failures: Fall back to physics-only predictions
- Prediction errors: Log error and use last known good prediction
- Feature extraction failures: Use default feature values
- Version mismatches: Load correct model version or retrain

### Database Errors
- Connection failures: Retry with backoff and queue writes
- Transaction timeouts: Rollback and retry operation
- Storage capacity: Trigger automatic archival
- Query failures: Log error and return cached results

### WebSocket Errors
- Connection drops: Automatic reconnection with exponential backoff
- Message delivery failures: Queue messages and retry
- Client disconnections: Clean up resources and log event
- Broadcast errors: Retry to failed clients individually

## Testing Strategy

### Unit Testing
The system will use pytest for Python backend testing and Jest for React frontend testing. Unit tests will cover:

- Individual component functions and methods
- Data validation logic
- Feature extraction algorithms
- API endpoint handlers
- Database operations
- Error handling paths

### Property-Based Testing
The system will use Hypothesis for Python property-based testing. The testing framework will:

- Run a minimum of 100 iterations per property test
- Generate random valid inputs across the full input space
- Verify universal properties hold for all generated inputs
- Tag each property test with the corresponding design document property number
- Use format: `# Feature: astrosense-space-weather, Property X: [property description]`

Each correctness property listed above will be implemented as a dedicated property-based test. The tests will use smart generators that:

- Constrain inputs to valid ranges (e.g., Kp-index 0-9, flare classes X/M/C/B/A)
- Generate edge cases (extreme values, boundary conditions)
- Create realistic space weather scenarios
- Produce synthetic anomalies for rare event testing

### Integration Testing
Integration tests will verify:

- End-to-end data flow from API to dashboard
- ML + Physics fusion pipeline
- Database persistence and retrieval
- WebSocket streaming functionality
- Alert generation and delivery
- Backtesting mode operation

### Performance Testing
Performance tests will validate:

- API response times under load
- Database query performance with large datasets
- WebSocket broadcast latency
- Dashboard rendering speed
- Alert generation timing (< 10 seconds for X-class flares)

### Acceptance Testing
Acceptance tests will verify each requirement from the requirements document by:

- Testing specific user scenarios
- Validating UI behavior and appearance
- Confirming alert thresholds and classifications
- Verifying calculation formulas and weightings
- Checking data accuracy and completeness
