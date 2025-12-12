# AstroSense - Space Weather Impact Forecasting System

A real-time space weather intelligence system that combines machine learning predictions with physics-based rules to forecast infrastructure impacts from solar events.

## Features

- **Real-time Data Collection**: Integrates with NASA DONKI and NOAA SWPC APIs
- **ML + Physics Fusion Engine**: Combines Random Forest ML with McPherron relation physics
- **Sector-Specific Predictions**: Aviation, Telecom, GPS, Power Grids, Satellites
- **Interactive Dashboard**: 3D Earth heatmap, real-time charts, alerts
- **Backtesting Mode**: Replay historical events (e.g., May 2024 geomagnetic storm)

## Tech Stack

### Backend
- **Framework**: FastAPI
- **ML**: scikit-learn (Random Forest)
- **Database**: PostgreSQL
- **Testing**: pytest, Hypothesis (property-based testing)

### Frontend
- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS
- **Visualizations**: Highcharts.js, Cesium.js
- **Real-time**: WebSocket

## Project Structure

```
astrosense/
├── backend/
│   ├── api/              # FastAPI endpoints
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── database/         # Database schema and manager
│   ├── tests/            # Unit and property-based tests
│   ├── ml_models/        # Trained ML models
│   ├── main.py           # FastAPI app entry point
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # Utilities and API clients
│   └── package.json      # Node dependencies
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- NASA API Key (get from https://api.nasa.gov/)

### Backend Setup

1. Create Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

4. Initialize database:
```bash
psql -U postgres -c "CREATE DATABASE astrosense_db;"
psql -U postgres -d astrosense_db -f database/schema.sql
```

5. Run the backend:
```bash
python main.py
```

Backend will be available at http://localhost:8000

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your API URLs
```

3. Run the development server:
```bash
npm run dev
```

Frontend will be available at http://localhost:3000

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /api/predict-impact` - Get sector-specific predictions
- `GET /api/fetch-data` - Get current space weather data
- `POST /api/backtest` - Run historical event replay
- `WS /api/stream` - WebSocket for real-time updates

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Property-Based Tests
```bash
pytest tests/ -k property
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Development Workflow

This project follows spec-driven development. See `.kiro/specs/astrosense-space-weather/` for:
- `requirements.md` - Detailed requirements with acceptance criteria
- `design.md` - System architecture and correctness properties
- `tasks.md` - Implementation task list

## License

MIT License - See LICENSE file for details

## Contributing

1. Follow the task list in `.kiro/specs/astrosense-space-weather/tasks.md`
2. Write property-based tests for all correctness properties
3. Ensure all tests pass before submitting PRs
4. Follow the coding standards defined in the design document

## Acknowledgments

- NASA DONKI API for space weather data
- NOAA SWPC for real-time solar wind measurements
- McPherron et al. for physics-based prediction models
