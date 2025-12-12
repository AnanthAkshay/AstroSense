# Implementation Plan

- [x] 1. Set up project structure and development environment




  - Create directory structure for backend (FastAPI), frontend (Next.js), ML models, and database
  - Initialize Python virtual environment and install core dependencies (FastAPI, scikit-learn, pandas, numpy, psycopg2, hypothesis)
  - Initialize Next.js project with TypeScript, Tailwind CSS, and install visualization libraries (Highcharts, Cesium.js)
  - Set up PostgreSQL database with initial schema
  - Configure environment variables for API keys and database connections
  - _Requirements: 1.1, 1.2, 14.1, 15.1_



- [ ] 2. Implement data ingestion layer






  - [x] 2.1 Create API client manager for NASA DONKI and NOAA SWPC

    - Implement HTTP client with retry logic and exponential backoff
    - Add response caching mechanism (60-second TTL)


    - Implement rate limiting to respect API quotas
    - Add error handling and logging for failed requests

    - _Requirements: 1.1, 1.2, 1.3, 1.5_

  - [x] 2.2 Write property test for API data parsing

    - **Property 1: API data parsing completeness**
    - **Validates: Requirements 1.1**



  - [x] 2.3 Write property test for NOAA data extraction


    - **Property 2: NOAA SWPC data extraction**
    - **Validates: Requirements 1.2**



  - [x] 2.4 Write property test for retry logic


    - **Property 3: Retry with exponential backoff**
    - **Validates: Requirements 1.3**



  - [x] 2.5 Write property test for response caching


    - **Property 4: Response caching consistency**
    - **Validates: Requirements 1.5**

- [x] 3. Implement data processing layer



  - [x] 3.1 Create validation engine




    - Implement field presence validation
    - Add numerical range validation for all space weather parameters
    - Implement timestamp chronology validation


    - Add validation failure logging
    - _Requirements: 20.1, 20.2, 20.4_

  - [x] 3.2 Create normalization engine





    - Implement min-max normalization for numerical features [0, 1]
    - Add flare class encoding (X=5, M=4, C=3, B=2, A=1)


    - Implement 6-hour median imputation for missing values
    - Preserve raw values alongside normalized values
    - _Requirements: 18.1, 18.2, 18.3, 18.5_

  - [x] 3.3 Create feature extraction engine



    - Extract 12-dimensional feature vectors from raw data
    - Compute derived features (Bz rate of change, wind speed variance)
    - Calculate temporal features (time since last flare, CME arrival proximity)


    - Add geomagnetic latitude and local time factors
    - _Requirements: 2.1, 18.4_

  - [x] 3.4 Write property tests for validation engine




    - **Property 73: Required field validation**



    - **Property 74: Numerical range validation**
    - **Property 75: Validation failure logging**
    - **Property 76: Timestamp chronology validation**
    - **Property 77: Data quality alerting**


    - **Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5**


  - [x] 3.5 Write property tests for normalization





    - **Property 63: Normalization output range**
    - **Property 64: Flare class encoding**
    - **Property 65: Missing value imputation**


    - **Property 67: Raw value preservation**
    - **Validates: Requirements 18.1, 18.2, 18.3, 18.5**

  - [x] 3.6 Write property test for feature extraction




    - **Property 5: Feature extraction completeness**



    - **Property 66: Feature vector dimensionality**
    - **Validates: Requirements 2.1, 18.4**



- [x] 4. Build ML model training pipeline









  - [x] 4.1 Create synthetic training data generator


    - Generate historical space weather scenarios


    - Inject synthetic anomalies (high-speed CMEs, extreme Bz, Kp spikes)
    - Label data with impact outcomes for supervised learning
    - Create train/validation/test splits
    - _Requirements: 2.2, 2.3_

  - [x] 4.2 Implement Random Forest training


    - Configure Random Forest Regressor with optimal hyperparameters
    - Train on at least 1000 labeled data points
    - Implement cross-validation for model selection
    - Save trained model with versioning metadata
    - _Requirements: 2.2, 2.4, 2.5_

  - [x] 4.3 Write property test for synthetic anomalies






    - **Property 7: Synthetic anomaly characteristics**
    - **Validates: Requirements 2.3**

  - [x] 4.4 Write property test for model serialization




    - **Property 6: Model serialization round-trip**
    - **Validates: Requirements 2.5**
-

- [x] 5. Implement physics rules engine






  - [x] 5.1 Create physics rules engine



    - Implement McPherron relation (Bz + wind speed correlation)
    - Add CME speed impact rules (speed > 1000 km/s amplification)
    - Implement X-class flare immediate blackout trigger
    - Weight physics predictions at 40%
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 5.2 Create fusion combiner



    - Combine ML (60%) and physics (40%) predictions
    - Implement conservative conflict resolution (choose higher risk)
    - Add discrepancy logging for analysis
    - _Requirements: 3.4, 3.5_

  - [x] 5.3 Write property tests for physics rules










    - **Property 8: McPherron relation application**
    - **Property 9: High-speed CME impact amplification**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 5.4 Write property tests for fusion






    - **Property 10: Fusion weighting formula**
    - **Property 11: Conservative conflict resolution**
    - **Validates: Requirements 3.4, 3.5**

- [x] 6. Implement sector-specific predictors



  - [x] 6.1 Create aviation predictor


    - Calculate HF blackout probability (0-100%)
    - Compute polar route risk based on Kp-index and latitude
    - Generate alerts when risk exceeds 70%
    - Include time windows for impact forecasts
    - _Requirements: 4.1, 4.2, 4.3, 4.5_


  - [x] 6.2 Create telecom predictor




    - Calculate signal degradation percentage (0-100%)
    - Implement moderate threshold (30%) and severe threshold (60%)
    - Generate warning and critical alerts
    - Estimate impact duration with start/end times
    - _Requirements: 5.1, 5.2, 5.3, 5.5_


  - [x] 6.3 Create GPS predictor






    - Calculate positional drift in centimeters
    - Implement moderate warning (50 cm) and critical warning (200 cm)
    - Determine geographic distribution of impacts
    - Identify regions with greatest drift

    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 6.4 Create power grid predictor





    - Calculate GIC risk level (1-10 scale)
    - Consider ground conductivity and grid topology
    - Generate high-risk alerts (level 7+) with recommendations

    - Provide 6-hour advance warning window
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [x] 6.5 Create satellite predictor





    - Calculate orbital drag risk (1-10 scale)
    - Generate alerts for risk level 6+ with maneuver recommendations
    - Provide altitude-specific impact predictions


    - Ensure 24-hour advance notice
    - Implement multi-satellite prioritization
    - _Requirements: 8.1, 8.2, 8.4, 8.5_


  - [x] 6.6 Write property tests for aviation predictor





    - **Property 12: Aviation risk output range**
    - **Property 13: Polar route risk sensitivity**
    - **Property 14: Aviation alert threshold**
    - **Validates: Requirements 4.1, 4.2, 4.3**


  - [x] 6.7 Write property tests for telecom predictor





    - **Property 15: Telecom degradation output range**
    - **Property 16: Telecom moderate threshold**
    - **Property 17: Telecom critical threshold**

    - **Validates: Requirements 5.1, 5.2, 5.3**

  - [x] 6.8 Write property tests for GPS predictor





    - **Property 18: GPS drift output units**
    - **Property 19: GPS moderate warning threshold**

    - **Property 20: GPS critical warning threshold**
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [x] 6.9 Write property tests for power grid predictor




    - **Property 21: GIC risk output range**
    - **Property 22: GIC high-risk alert threshold**
    - **Property 23: GIC calculation inputs**
    - **Validates: Requirements 7.1, 7.2, 7.4**

  - [x] 6.10 Write property tests for satellite predictor




    - **Property 24: Satellite drag risk output range**
    - **Property 25: Satellite drag alert threshold**
    - **Property 26: Multi-satellite alert prioritization**
    - **Validates: Requirements 8.1, 8.2, 8.5**

- [x] 7. Implement composite score calculator



  - [x] 7.1 Create composite score calculator


    - Implement weighted formula: 0.35×Aviation + 0.25×Telecom + 0.20×GPS + 0.20×PowerGrid
    - Scale output to 0-100 range
    - Classify severity (low/moderate/high)
    - Generate system-wide alerts for scores > 70
    - Log score changes with timestamps and contributing factors
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

  - [x] 7.2 Write property tests for composite scoring


    - **Property 68: Composite score calculation formula**
    - **Property 69: Composite score output range**
    - **Property 70: High composite score alert**
    - **Property 71: Composite score change logging**
    - **Validates: Requirements 19.1, 19.2, 19.3, 19.4**

- [x] 8. Checkpoint - Ensure all backend core logic tests pass




  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement alert management system



  - [x] 9.1 Create alert manager


    - Generate flash alerts for X-class flares (< 10 seconds)
    - Create impact forecasts for CMEs with confidence intervals
    - Prioritize alerts by severity then chronological order
    - Implement 2-hour alert expiration and history archival
    - Include mitigation recommendations in alerts
    - _Requirements: 11.1, 11.3, 11.4, 11.5, 12.1, 12.2_

  - [x] 9.2 Write property tests for alert management


    - **Property 34: Flash alert generation speed**
    - **Property 35: Flash alert content completeness**
    - **Property 36: Alert prioritization and ordering**
    - **Property 37: Alert expiration lifecycle**
    - **Property 38: CME forecast confidence interval**
    - **Property 39: Impact forecast content completeness**
    - **Validates: Requirements 11.1, 11.3, 11.4, 11.5, 12.1, 12.2**

- [x] 10. Implement database layer




  - [x] 10.1 Create database schema and manager


    - Design tables for space weather data, predictions, alerts, and backtest results
    - Implement database manager with CRUD operations
    - Add indexing on timestamp and event type fields
    - Implement automatic archival for data > 1 year when storage > 80%
    - Ensure write transactions complete within 500ms
    - _Requirements: 14.1, 14.2, 14.3, 14.5_

  - [x] 10.2 Write property tests for database operations


    - **Property 47: Data persistence with metadata**
    - **Property 48: Prediction storage with versioning**
    - **Property 49: Database write performance**
    - **Property 50: Automatic data archival**
    - **Property 72: Historical composite score retrieval**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.5, 19.5**

- [-] 11. Implement FastAPI backend endpoints



  - [x] 11.1 Create REST API endpoints


    - POST /api/predict-impact: Accept input data, return sector predictions as JSON
    - GET /api/fetch-data: Return current space weather measurements as JSON
    - POST /api/backtest: Accept event date, return historical replay data as JSON
    - Implement rate limiting with HTTP 429 responses
    - Add CORS headers to all responses
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 11.2 Implement WebSocket streaming endpoint


    - Create WS /api/stream endpoint for real-time updates
    - Establish connections within 2 seconds
    - Push updates to all connected clients simultaneously
    - Send updates at intervals ≤ 10 seconds
    - Implement automatic reconnection with exponential backoff
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [x] 11.3 Write property tests for API endpoints


    - **Property 51: Predict-impact endpoint response format**
    - **Property 52: Fetch-data endpoint response format**
    - **Property 53: Backtest endpoint response format**
    - **Property 54: Rate limit HTTP response**
    - **Property 55: CORS header inclusion**
    - **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.5**

  - [x] 11.4 Write property tests for WebSocket streaming



    - **Property 58: Real-time data push**
    - **Property 59: Connection establishment performance**
    - **Property 60: Update frequency constraint**
    - **Property 61: Automatic reconnection with backoff**
    - **Property 62: Broadcast to multiple clients**
    - **Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5**

- [x] 12. Implement backtesting functionality





  - [x] 12.1 Create backtesting engine


    - Load historical data from May 2024 geomagnetic storm
    - Replay events in chronological order with adjustable speed
    - Display predictions alongside actual observed impacts
    - Generate accuracy report comparing predictions to ground truth
    - Support mode switching without page reload
    - Log post-event accuracy metrics
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 12.5_

  - [x] 12.2 Write property tests for backtesting



    - **Property 43: Backtesting chronological replay**
    - **Property 44: Backtesting prediction and actual display**
    - **Property 45: Backtesting accuracy report generation**
    - **Property 46: Backtesting mode exit without reload**
    - **Property 42: Post-event accuracy logging**
    - **Validates: Requirements 13.2, 13.3, 13.4, 13.5, 12.5**

- [ ] 13. Checkpoint - Ensure all backend tests pass



  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Build frontend dashboard structure
  - [ ] 14.1 Create Next.js app structure and layout
    - Set up Next.js pages and routing
    - Create main dashboard layout with dark theme
    - Apply Tailwind CSS styling with blue/cyan accents
    - Implement responsive design for mobile (< 768px)
    - Add animation timing constraints (200-400ms)
    - _Requirements: 16.1, 16.4, 16.5_

  - [ ] 14.2 Create API client for backend communication
    - Implement fetch wrappers for REST endpoints
    - Add WebSocket client for real-time streaming
    - Handle connection errors and reconnection
    - Implement data caching and state management
    - _Requirements: 15.1, 17.1_

  - [ ] 14.3 Write property tests for UI responsiveness
    - **Property 56: Animation timing constraints**
    - **Property 57: Mobile responsive layout**
    - **Validates: Requirements 16.4, 16.5**

- [ ] 15. Implement dashboard visualization components
  - [ ] 15.1 Create 3D heatmap component with Cesium.js
    - Initialize 3D Earth globe with geomagnetic latitude shading
    - Implement color-coded risk mapping (green/yellow/red)
    - Add rotation, zoom, and region selection interactions
    - Display detailed metrics on region selection
    - Refresh visualization within 2 seconds on data updates
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ] 15.2 Create time-series charts with Highcharts.js
    - Plot solar wind speed in km/s
    - Plot Bz magnetic field in nT
    - Display 24 hours of data with 5-minute resolution
    - Highlight and annotate critical threshold crossings
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ] 15.3 Create risk cards component
    - Display aviation HF blackout probability and polar risk
    - Show telecom signal degradation percentage
    - Display GPS drift in centimeters
    - Show power grid GIC risk level (1-10)
    - Display satellite orbital drag risk (1-10)
    - Apply color-coded severity indicators
    - _Requirements: 4.4, 5.4, 6.4, 7.3, 8.3_

  - [ ] 15.4 Create alerts panel component
    - Display flash alerts prominently with audio notification
    - Show impact forecasts with countdown timers
    - Implement alert prioritization and sorting
    - Move expired alerts to history section
    - Display uncertainty levels for low-confidence forecasts
    - _Requirements: 11.2, 11.3, 12.3, 12.4_

  - [ ] 15.5 Create impact table component
    - Display sector-specific predictions in tabular format
    - Show time windows for predicted impacts
    - Include geographic distribution information
    - Display mitigation recommendations
    - _Requirements: 4.5, 5.5, 6.5, 7.3_

  - [ ] 15.6 Create backtesting controls component
    - Add playback controls (play/pause/speed adjustment)
    - Display predictions vs actual impacts side-by-side
    - Show accuracy metrics and comparison charts
    - Implement mode switching button
    - _Requirements: 13.2, 13.3, 13.4, 13.5_

  - [ ] 15.7 Write property tests for heatmap
    - **Property 27: Risk severity color mapping**
    - **Property 28: Region selection detail display**
    - **Property 29: Heatmap update performance**
    - **Validates: Requirements 9.2, 9.4, 9.5**

  - [ ] 15.8 Write property tests for charts
    - **Property 30: Solar wind chart units**
    - **Property 31: Bz chart units**
    - **Property 32: Chart time window and resolution**
    - **Property 33: Threshold visualization**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

  - [ ] 15.9 Write property tests for alerts display
    - **Property 40: Forecast countdown display**
    - **Property 41: Low confidence uncertainty indication**
    - **Validates: Requirements 12.3, 12.4**

- [ ] 16. Integrate real-time data streaming
  - [ ] 16.1 Connect WebSocket to dashboard components
    - Subscribe to real-time updates on component mount
    - Update heatmap, charts, and cards on new data
    - Handle connection loss and reconnection
    - Display connection status indicator
    - _Requirements: 17.1, 17.4_

  - [ ] 16.2 Implement live data refresh logic
    - Update all visualizations without page reload
    - Animate new data points smoothly
    - Maintain user interactions during updates
    - Queue updates during user interactions
    - _Requirements: 9.5, 10.5_

- [ ] 17. Final checkpoint - End-to-end testing
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Create deployment configuration
  - [ ] 18.1 Set up production environment
    - Configure production database with connection pooling
    - Set up environment variables for production
    - Configure CORS for production domain
    - Set up logging and monitoring
    - _Requirements: 15.5, 14.1_

  - [ ] 18.2 Create Docker containers
    - Create Dockerfile for FastAPI backend
    - Create Dockerfile for Next.js frontend
    - Create docker-compose.yml for orchestration
    - Configure PostgreSQL container
    - _Requirements: All_

  - [ ] 18.3 Write deployment documentation
    - Document environment setup steps
    - Provide API key configuration instructions
    - Document database migration process
    - Create troubleshooting guide
    - _Requirements: All_
