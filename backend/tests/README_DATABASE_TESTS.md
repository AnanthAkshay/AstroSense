# Database Property Tests

This document describes how to run the database property-based tests for AstroSense.

## Prerequisites

1. PostgreSQL database (version 15 or higher)
2. Python dependencies installed (`pip install -r requirements.txt`)

## Setting Up Test Database

### Option 1: Using Docker Compose (Recommended)

1. Start the PostgreSQL container:
```bash
docker-compose up -d postgres
```

2. Wait for the database to be ready (check with `docker-compose ps`)

3. Set the test database URL environment variable:
```bash
export TEST_DATABASE_URL="postgresql://astrosense:astrosense_password@localhost:5432/astrosense_db"
```

On Windows PowerShell:
```powershell
$env:TEST_DATABASE_URL="postgresql://astrosense:astrosense_password@localhost:5432/astrosense_db"
```

### Option 2: Using Local PostgreSQL

1. Create a test database:
```sql
CREATE DATABASE astrosense_test;
CREATE USER astrosense_test WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE astrosense_test TO astrosense_test;
```

2. Initialize the schema:
```bash
psql -U astrosense_test -d astrosense_test -f backend/database/schema.sql
```

3. Set the test database URL:
```bash
export TEST_DATABASE_URL="postgresql://astrosense_test:test_password@localhost:5432/astrosense_test"
```

## Running the Tests

### Run all database property tests:
```bash
cd backend
python -m pytest tests/test_database_properties.py -v
```

### Run a specific property test:
```bash
python -m pytest tests/test_database_properties.py::test_property_47_data_persistence_with_metadata -v
```

### Run with Hypothesis statistics:
```bash
python -m pytest tests/test_database_properties.py -v --hypothesis-show-statistics
```

## Property Tests Included

1. **Property 47**: Data persistence with metadata (Requirements 14.1)
2. **Property 48**: Prediction storage with versioning (Requirements 14.2)
3. **Property 49**: Database write performance (Requirements 14.3)
4. **Property 50**: Automatic data archival (Requirements 14.5)
5. **Property 72**: Historical composite score retrieval (Requirements 19.5)

## Test Behavior

- If `TEST_DATABASE_URL` is not set, all tests will be **skipped** automatically
- Tests use a cleanup fixture to remove test data after each test
- Each property test runs 100 examples by default (configurable via Hypothesis settings)
- Write performance tests have a 500ms deadline requirement

## Troubleshooting

### Tests are skipped
- Ensure `TEST_DATABASE_URL` environment variable is set
- Verify database is running and accessible

### Connection errors
- Check database credentials in the connection string
- Verify PostgreSQL is listening on the correct port
- Ensure firewall allows connections to PostgreSQL

### Schema errors
- Run the schema initialization script: `psql -f backend/database/schema.sql`
- Verify all tables exist: `\dt` in psql

### Performance test failures
- Database write performance depends on hardware and load
- If tests consistently fail, check database configuration and system resources
- Consider adjusting the 500ms threshold if running on slower hardware (though this violates requirements)
