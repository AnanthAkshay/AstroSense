# AstroSense Database Layer

This module provides comprehensive database management for the AstroSense space weather forecasting system.

## Overview

The database layer implements:
- Connection pooling for high performance
- CRUD operations for all data types
- Automatic data archival
- Transaction management with 500ms timeout requirement
- Indexed queries for fast retrieval

## Components

### Database Manager (`manager.py`)

The `DatabaseManager` class provides:

#### Connection Management
- Connection pooling with configurable size
- Context managers for safe connection/cursor handling
- Automatic commit/rollback on errors

#### Data Operations

**Space Weather Data**
- `insert_space_weather_data()` - Store measurements with metadata
- `get_space_weather_data()` - Query with time/source filters

**CME Events**
- `insert_cme_event()` - Store CME predictions
- `get_cme_events()` - Query CME events

**Solar Flares**
- `insert_solar_flare()` - Store flare events
- `get_solar_flares()` - Query flares by time/class

**Predictions**
- `insert_prediction()` - Store sector predictions with versioning
- `get_predictions()` - Query predictions by time

**Alerts**
- `insert_alert()` - Store alerts
- `get_active_alerts()` - Get non-expired alerts
- `archive_expired_alerts()` - Archive old alerts

**Composite Scores**
- `insert_composite_score_history()` - Store score history
- `get_composite_score_history()` - Query for trend analysis

**Backtesting**
- `insert_backtest_result()` - Store backtest results
- `get_backtest_results()` - Query backtest data

#### Data Archival
- `check_storage_usage()` - Monitor database size
- `archive_old_data()` - Remove data older than 1 year
- `auto_archive_if_needed()` - Automatic archival at 80% capacity

## Data Models

### Space Weather Models (`models/space_weather.py`)
- `SpaceWeatherData` - Solar wind, Bz, Kp-index, proton flux
- `CMEEvent` - CME detection and arrival predictions
- `SolarFlare` - Solar flare classifications

### Prediction Models (`models/prediction.py`)
- `SectorPredictions` - Aviation, telecom, GPS, power, satellite risks
- `CompositeScoreHistory` - Overall risk scores with contributions
- `BacktestResult` - Historical event validation data

### Alert Models (`models/alert.py`)
- `Alert` - Base alert structure
- `FlashAlert` - Immediate X-class flare alerts
- `ImpactForecast` - CME impact predictions

## Database Schema

The schema includes the following tables:

1. **space_weather_data** - Raw measurements
2. **cme_events** - CME detections and predictions
3. **solar_flares** - Flare events
4. **predictions** - Sector-specific predictions
5. **alerts** - Alert notifications
6. **composite_score_history** - Historical risk scores
7. **backtest_results** - Validation data

All tables include:
- Indexed timestamp fields for fast queries
- Appropriate constraints and foreign keys
- JSONB fields for flexible metadata storage

## Usage Example

```python
from database import DatabaseManager
from models.space_weather import SpaceWeatherData
from datetime import datetime

# Initialize manager
db = DatabaseManager()

# Insert data
data = SpaceWeatherData(
    timestamp=datetime.utcnow(),
    solar_wind_speed=450.0,
    bz_field=-8.5,
    kp_index=5.0,
    proton_flux=150.0,
    source="NOAA_SWPC"
)

record_id = db.insert_space_weather_data(data)

# Query data
recent_data = db.get_space_weather_data(
    start_time=datetime.utcnow() - timedelta(hours=24),
    limit=1000
)

# Automatic archival
db.auto_archive_if_needed()

# Close connections
db.close()
```

## Configuration

Set the following environment variables:

```bash
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Performance

The database layer is designed to meet the following requirements:

- **Write Performance**: All transactions complete within 500ms (Requirement 14.3)
- **Connection Pooling**: Reuses connections for efficiency
- **Indexed Queries**: Fast retrieval using timestamp and type indexes
- **Automatic Archival**: Maintains performance by removing old data (Requirement 14.5)

## Testing

Property-based tests verify:
- Data persistence with metadata (Property 47)
- Prediction storage with versioning (Property 48)
- Write performance under 500ms (Property 49)
- Automatic archival at 80% capacity (Property 50)
- Historical score retrieval (Property 72)

See `tests/README_DATABASE_TESTS.md` for testing instructions.

## Requirements Validation

This implementation validates the following requirements:

- **14.1**: Data persistence with timestamp and source metadata
- **14.2**: Prediction storage with model version and input features
- **14.3**: Write transactions complete within 500ms
- **14.4**: Indexed queries on timestamp and event type fields
- **14.5**: Automatic archival of data older than 1 year at 80% capacity
- **19.5**: Historical composite score retrieval for trend analysis
