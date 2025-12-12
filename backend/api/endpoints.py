"""
FastAPI REST API Endpoints for AstroSense
Provides REST endpoints for predictions, data fetching, and backtesting
"""
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
import time
from collections import defaultdict

from services.api_client import api_client
from services.sector_predictors import (
    aviation_predictor,
    telecom_predictor,
    gps_predictor,
    power_grid_predictor,
    satellite_predictor,
    composite_score_calculator
)
from services.fusion_combiner import fusion_combiner
from services.backtesting_engine import backtesting_engine
from database.manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["api"])

# Rate limiting storage (in-memory for simplicity)
rate_limit_storage = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


# ==================== Request/Response Models ====================

class PredictImpactRequest(BaseModel):
    """Request model for predict-impact endpoint"""
    solar_wind_speed: Optional[float] = Field(default=400.0, description="Solar wind speed in km/s")
    bz: Optional[float] = Field(default=0.0, description="Bz magnetic field in nT")
    kp_index: Optional[float] = Field(default=3.0, description="Kp-index (0-9)")
    proton_flux: Optional[float] = Field(default=0.0, description="Proton flux")
    flare_class: Optional[str] = Field(default="", description="Solar flare class (X, M, C, B, A)")
    cme_speed: Optional[float] = Field(default=0.0, description="CME speed in km/s")
    geomagnetic_latitude: Optional[float] = Field(default=70.0, description="Geomagnetic latitude")
    ground_conductivity: Optional[float] = Field(default=0.5, description="Ground conductivity (0-1)")
    grid_topology_factor: Optional[float] = Field(default=1.0, description="Grid topology factor")
    altitude_km: Optional[float] = Field(default=400.0, description="Satellite altitude in km")


class BacktestRequest(BaseModel):
    """Request model for backtest endpoint"""
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    event_name: Optional[str] = Field(default="Historical Event", description="Name of the event")


class BacktestControlRequest(BaseModel):
    """Request model for backtest control endpoints"""
    action: str = Field(..., description="Control action: play, pause, stop, speed")
    speed: Optional[float] = Field(default=1.0, description="Replay speed multiplier")


# ==================== Rate Limiting ====================

def check_rate_limit(client_id: str) -> bool:
    """
    Check if client has exceeded rate limit
    
    Args:
        client_id: Client identifier (IP address)
        
    Returns:
        True if within rate limit, False if exceeded
    """
    current_time = time.time()
    
    # Clean old requests outside the window
    rate_limit_storage[client_id] = [
        req_time for req_time in rate_limit_storage[client_id]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[client_id]) >= RATE_LIMIT:
        return False
    
    # Add current request
    rate_limit_storage[client_id].append(current_time)
    return True


def rate_limit_middleware(request: Request):
    """
    Middleware to enforce rate limiting
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_id = request.client.host
    
    if not check_rate_limit(client_id):
        # Calculate retry-after time
        oldest_request = min(rate_limit_storage[client_id])
        retry_after = int(RATE_LIMIT_WINDOW - (time.time() - oldest_request)) + 1
        
        logger.warning(f"Rate limit exceeded for client {client_id}")
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


# ==================== API Endpoints ====================

@router.post("/predict-impact")
async def predict_impact(
    request: Request,
    data: PredictImpactRequest
) -> Dict[str, Any]:
    """
    POST /api/predict-impact
    
    Accept input data and return sector-specific predictions as JSON
    
    Args:
        request: FastAPI request object
        data: Input space weather data
        
    Returns:
        JSON with sector-specific risk predictions
        
    Validates: Requirements 15.1
    """
    # Check rate limit
    rate_limit_middleware(request)
    
    try:
        logger.info("Processing predict-impact request")
        
        # Prepare space weather data
        space_weather_data = {
            'solar_wind_speed': data.solar_wind_speed,
            'bz': data.bz,
            'kp_index': data.kp_index,
            'proton_flux': data.proton_flux,
            'flare_class': data.flare_class,
            'cme_speed': data.cme_speed
        }
        
        # Generate predictions for each sector
        aviation_pred = aviation_predictor.predict(
            space_weather_data,
            geomagnetic_latitude=data.geomagnetic_latitude
        )
        
        telecom_pred = telecom_predictor.predict(space_weather_data)
        
        gps_pred = gps_predictor.predict(space_weather_data)
        
        power_grid_pred = power_grid_predictor.predict(
            space_weather_data,
            ground_conductivity=data.ground_conductivity,
            grid_topology_factor=data.grid_topology_factor
        )
        
        satellite_pred = satellite_predictor.predict(
            space_weather_data,
            altitude_km=data.altitude_km
        )
        
        # Calculate composite score
        sector_predictions = {
            'aviation': aviation_pred,
            'telecom': telecom_pred,
            'gps': gps_pred,
            'power_grid': power_grid_pred,
            'satellite': satellite_pred
        }
        
        composite_result = composite_score_calculator.calculate(sector_predictions)
        
        # Prepare response
        response = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'predictions': {
                'aviation': {
                    'hf_blackout_probability': aviation_pred['hf_blackout_probability'],
                    'polar_route_risk': aviation_pred['polar_route_risk'],
                    'alert': aviation_pred.get('alert'),
                    'impact_window': aviation_pred.get('impact_window')
                },
                'telecommunications': {
                    'signal_degradation_percent': telecom_pred['signal_degradation_percent'],
                    'classification': telecom_pred['classification'],
                    'alert': telecom_pred.get('alert'),
                    'impact_duration': telecom_pred.get('impact_duration')
                },
                'gps': {
                    'positional_drift_cm': gps_pred['positional_drift_cm'],
                    'classification': gps_pred['classification'],
                    'geographic_distribution': gps_pred.get('geographic_distribution'),
                    'alert': gps_pred.get('alert')
                },
                'power_grid': {
                    'gic_risk_level': power_grid_pred['gic_risk_level'],
                    'classification': power_grid_pred['classification'],
                    'alert': power_grid_pred.get('alert'),
                    'warning_window': power_grid_pred.get('warning_window')
                },
                'satellite': {
                    'orbital_drag_risk': satellite_pred['orbital_drag_risk'],
                    'altitude_km': satellite_pred['altitude_km'],
                    'classification': satellite_pred['classification'],
                    'alert': satellite_pred.get('alert'),
                    'advance_notice': satellite_pred.get('advance_notice')
                }
            },
            'composite': {
                'score': composite_result['composite_score'],
                'severity': composite_result['severity'],
                'contributing_factors': composite_result['contributing_factors'],
                'alert': composite_result.get('alert')
            }
        }
        
        logger.info(f"Predict-impact completed: composite score {composite_result['composite_score']:.1f}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in predict-impact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/fetch-data")
async def fetch_data(request: Request) -> Dict[str, Any]:
    """
    GET /api/fetch-data
    
    Return current space weather measurements as JSON
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON with current space weather data
        
    Validates: Requirements 15.2
    """
    # Check rate limit
    rate_limit_middleware(request)
    
    try:
        logger.info("Processing fetch-data request")
        
        # Fetch all space weather data
        data = await api_client.fetch_all_space_weather_data()
        logger.info(f"Fetched data: {data}")
        
        # Extract and format the data
        response = {
            'timestamp': data.get('timestamp'),
            'solar_wind': {
                'speed': data.get('solar_wind', {}).get('speed'),
                'density': data.get('solar_wind', {}).get('density'),
                'temperature': data.get('solar_wind', {}).get('temperature'),
                'timestamp': data.get('solar_wind', {}).get('timestamp')
            },
            'magnetic_field': {
                'bx': data.get('magnetic_field', {}).get('bx'),
                'by': data.get('magnetic_field', {}).get('by'),
                'bz': data.get('magnetic_field', {}).get('bz'),
                'bt': data.get('magnetic_field', {}).get('bt'),
                'timestamp': data.get('magnetic_field', {}).get('timestamp')
            },
            'kp_index': {
                'value': data.get('kp_index', {}).get('kp_index'),
                'timestamp': data.get('kp_index', {}).get('timestamp')
            },
            'cme_events': data.get('cme_events', {}).get('events', []),
            'solar_flares': data.get('solar_flares', {}).get('events', [])
        }
        
        logger.info("Fetch-data completed successfully")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in fetch-data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data fetch failed: {str(e)}"
        )


@router.post("/backtest")
async def backtest(
    request: Request,
    data: BacktestRequest
) -> Dict[str, Any]:
    """
    POST /api/backtest
    
    Accept event date and return historical replay data as JSON
    
    Args:
        request: FastAPI request object
        data: Backtest request with event date
        
    Returns:
        JSON with historical event replay data
        
    Validates: Requirements 15.3
    """
    # Check rate limit
    rate_limit_middleware(request)
    
    try:
        logger.info(f"Processing backtest request for {data.event_date}")
        
        # Parse event date
        try:
            event_date = datetime.strptime(data.event_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Load historical data using backtesting engine
        timeline = await backtesting_engine.load_historical_data(event_date, data.event_name)
        
        # Replay events to generate predictions and comparisons
        replay_results = await backtesting_engine.replay_events(timeline, speed=10.0)  # Fast replay for API
        
        # Display predictions alongside actual impacts
        display_data = backtesting_engine.display_predictions_and_actual(timeline)
        
        # Generate accuracy report
        accuracy_report = backtesting_engine.generate_accuracy_report(timeline)
        
        # Log post-event accuracy metrics
        await backtesting_engine.log_post_event_accuracy(data.event_name, accuracy_report)
        
        # Extract predicted and actual impacts from timeline for response format
        predicted_impacts = {}
        actual_impacts = {}
        accuracy_metrics = {}
        
        # Get the latest measurement event with predictions
        measurement_events = [e for e in replay_results['timeline'] 
                            if e.get('event_type') == 'measurement' 
                            and e.get('predicted_impacts') 
                            and e.get('actual_impacts')]
        
        if measurement_events:
            latest_event = measurement_events[-1]
            predicted_impacts = latest_event['predicted_impacts']
            actual_impacts = latest_event['actual_impacts']
            
            # Calculate simple accuracy metrics
            accuracy_metrics = {
                'aviation_error': abs(predicted_impacts.get('aviation', {}).get('hf_blackout_probability', 0) - 
                                   actual_impacts.get('aviation', {}).get('hf_blackout_probability', 0)),
                'telecom_error': abs(predicted_impacts.get('telecommunications', {}).get('signal_degradation_percent', 0) - 
                                   actual_impacts.get('telecommunications', {}).get('signal_degradation_percent', 0)),
                'gps_error': abs(predicted_impacts.get('gps', {}).get('positional_drift_cm', 0) - 
                               actual_impacts.get('gps', {}).get('positional_drift_cm', 0)),
                'power_grid_error': abs(predicted_impacts.get('power_grid', {}).get('gic_risk_level', 0) - 
                                      actual_impacts.get('power_grid', {}).get('gic_risk_level', 0)),
                'satellite_error': abs(predicted_impacts.get('satellite', {}).get('orbital_drag_risk', 0) - 
                                     actual_impacts.get('satellite', {}).get('orbital_drag_risk', 0)),
                'composite_error': abs(predicted_impacts.get('composite_score', 0) - 
                                     actual_impacts.get('composite_score', 0))
            }
        else:
            # Provide default structure if no measurement events
            predicted_impacts = {
                'aviation': {'hf_blackout_probability': 0},
                'telecommunications': {'signal_degradation_percent': 0},
                'gps': {'positional_drift_cm': 0},
                'power_grid': {'gic_risk_level': 1},
                'satellite': {'orbital_drag_risk': 1},
                'composite_score': 0
            }
            actual_impacts = predicted_impacts.copy()
            accuracy_metrics = {
                'aviation_error': 0,
                'telecom_error': 0,
                'gps_error': 0,
                'power_grid_error': 0,
                'satellite_error': 0,
                'composite_error': 0
            }
        
        # Prepare response
        response = {
            'event_name': data.event_name,
            'event_date': event_date.isoformat(),
            'timeline': [
                {
                    'timestamp': event['timestamp'],
                    'event_type': event['event_type'],
                    'data': event['data'],
                    'predicted_impacts': event.get('predicted_impacts'),
                    'actual_impacts': event.get('actual_impacts')
                }
                for event in replay_results['timeline']
            ],
            'predicted_impacts': predicted_impacts,
            'actual_impacts': actual_impacts,
            'accuracy_metrics': accuracy_metrics,
            'display_data': display_data,
            'accuracy_report': accuracy_report,
            'replay_summary': {
                'events_processed': replay_results['events_processed'],
                'predictions_generated': replay_results['predictions_generated'],
                'duration_simulated_hours': len(timeline) * 2 if timeline else 0  # 2-hour intervals
            },
            'mode_switching': backtesting_engine.support_mode_switching()
        }
        
        logger.info(f"Backtest completed for {data.event_date}: {replay_results['events_processed']} events processed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}"
        )


@router.post("/backtest/control")
async def backtest_control(
    request: Request,
    data: BacktestControlRequest
) -> Dict[str, Any]:
    """
    POST /api/backtest/control
    
    Control backtesting playback (play, pause, stop, speed adjustment)
    
    Args:
        request: FastAPI request object
        data: Control request with action and parameters
        
    Returns:
        JSON with control response and current status
    """
    # Check rate limit
    rate_limit_middleware(request)
    
    try:
        logger.info(f"Processing backtest control: {data.action}")
        
        if data.action == "play":
            backtesting_engine.resume_replay()
            message = "Replay resumed"
        elif data.action == "pause":
            backtesting_engine.pause_replay()
            message = "Replay paused"
        elif data.action == "stop":
            backtesting_engine.pause_replay()
            backtesting_engine.current_position = 0
            message = "Replay stopped and reset"
        elif data.action == "speed":
            backtesting_engine.set_replay_speed(data.speed)
            message = f"Replay speed set to {data.speed}x"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {data.action}. Use play, pause, stop, or speed"
            )
        
        # Get current status
        status_info = backtesting_engine.get_replay_status()
        
        response = {
            'action': data.action,
            'message': message,
            'status': status_info,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in backtest control: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest control failed: {str(e)}"
        )


@router.get("/backtest/status")
async def backtest_status(request: Request) -> Dict[str, Any]:
    """
    GET /api/backtest/status
    
    Get current backtesting status and mode switching information
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON with current backtesting status
    """
    # Check rate limit
    rate_limit_middleware(request)
    
    try:
        status_info = backtesting_engine.get_replay_status()
        mode_switching = backtesting_engine.support_mode_switching()
        
        response = {
            'replay_status': status_info,
            'mode_switching': mode_switching,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting backtest status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval failed: {str(e)}"
        )


@router.get("/health")
async def api_health_check() -> Dict[str, str]:
    """
    GET /api/health
    
    Simple health check endpoint
    
    Returns:
        JSON with health status
    """
    return {"status": "healthy"}