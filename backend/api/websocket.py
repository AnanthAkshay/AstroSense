"""
WebSocket Streaming Endpoint for AstroSense
Provides real-time space weather updates to connected clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime

from services.api_client import api_client
from services.sector_predictors import (
    aviation_predictor,
    telecom_predictor,
    gps_predictor,
    power_grid_predictor,
    satellite_predictor,
    composite_score_calculator
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["websocket"])

# Connection manager for WebSocket clients
class ConnectionManager:
    """
    Manages WebSocket connections and broadcasts updates
    
    Features:
    - Track active connections
    - Broadcast updates to all clients simultaneously
    - Handle connection/disconnection
    - Automatic reconnection support
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.update_interval = 10  # seconds
        self.is_streaming = False
    
    async def connect(self, websocket: WebSocket) -> bool:
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            True if connection established within 2 seconds
            
        Validates: Requirements 17.2
        """
        try:
            # Set timeout for connection establishment
            await asyncio.wait_for(
                websocket.accept(),
                timeout=2.0
            )
            self.active_connections.append(websocket)
            logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
            return True
        except asyncio.TimeoutError:
            logger.error("WebSocket connection timeout (>2 seconds)")
            return False
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            return False
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast message to all connected clients simultaneously
        
        Args:
            message: Dictionary to send as JSON
            
        Validates: Requirements 17.1, 17.5
        """
        if not self.active_connections:
            return
        
        # Convert message to JSON
        json_message = json.dumps(message)
        
        # Send to all clients simultaneously
        disconnected = []
        
        # Use asyncio.gather to send to all clients at once
        send_tasks = []
        for connection in self.active_connections:
            send_tasks.append(self._send_to_client(connection, json_message))
        
        # Wait for all sends to complete
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # Track disconnected clients
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                disconnected.append(self.active_connections[i])
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
        
        if disconnected:
            logger.warning(f"Removed {len(disconnected)} disconnected clients during broadcast")
        else:
            logger.debug(f"Broadcast sent to {len(self.active_connections)} clients")
    
    async def _send_to_client(self, websocket: WebSocket, message: str):
        """
        Send message to a single client
        
        Args:
            websocket: WebSocket connection
            message: JSON string to send
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {str(e)}")
            raise
    
    async def start_streaming(self):
        """
        Start streaming space weather updates
        
        Continuously fetches data and broadcasts to clients
        Updates sent at intervals ≤ 10 seconds
        
        Validates: Requirements 17.3, 17.4
        """
        self.is_streaming = True
        logger.info("Started WebSocket streaming")
        
        while self.is_streaming:
            try:
                # Fetch current space weather data
                space_weather_data = await api_client.fetch_all_space_weather_data()
                
                # Extract key measurements
                solar_wind = space_weather_data.get('solar_wind', {})
                mag_field = space_weather_data.get('magnetic_field', {})
                kp_data = space_weather_data.get('kp_index', {})
                
                # Prepare data for predictions
                prediction_input = {
                    'solar_wind_speed': solar_wind.get('speed', 400.0),
                    'bz': mag_field.get('bz', 0.0),
                    'kp_index': kp_data.get('kp_index', 3.0),
                    'proton_flux': 0.0,  # Would need additional API call
                    'flare_class': '',
                    'cme_speed': 0.0
                }
                
                # Check for recent flares
                solar_flares = space_weather_data.get('solar_flares', {}).get('events', [])
                if solar_flares and isinstance(solar_flares, list) and len(solar_flares) > 0:
                    latest_flare = solar_flares[-1]
                    if isinstance(latest_flare, dict):
                        prediction_input['flare_class'] = latest_flare.get('classType', '')
                
                # Check for recent CMEs
                cme_events = space_weather_data.get('cme_events', {}).get('events', [])
                if cme_events and isinstance(cme_events, list) and len(cme_events) > 0:
                    latest_cme = cme_events[-1]
                    if isinstance(latest_cme, dict):
                        # CME speed might be in different fields
                        cme_analyses = latest_cme.get('cmeAnalyses', [])
                        if cme_analyses and len(cme_analyses) > 0:
                            prediction_input['cme_speed'] = cme_analyses[0].get('speed', 0.0)
                
                # Generate predictions
                aviation_pred = aviation_predictor.predict(prediction_input)
                telecom_pred = telecom_predictor.predict(prediction_input)
                gps_pred = gps_predictor.predict(prediction_input)
                power_grid_pred = power_grid_predictor.predict(prediction_input)
                satellite_pred = satellite_predictor.predict(prediction_input)
                
                sector_predictions = {
                    'aviation': aviation_pred,
                    'telecom': telecom_pred,
                    'gps': gps_pred,
                    'power_grid': power_grid_pred,
                    'satellite': satellite_pred
                }
                
                composite_result = composite_score_calculator.calculate(sector_predictions)
                
                # Prepare update message
                update = {
                    'type': 'space_weather_update',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': {
                        'solar_wind': {
                            'speed': solar_wind.get('speed'),
                            'density': solar_wind.get('density'),
                            'temperature': solar_wind.get('temperature')
                        },
                        'magnetic_field': {
                            'bx': mag_field.get('bx'),
                            'by': mag_field.get('by'),
                            'bz': mag_field.get('bz'),
                            'bt': mag_field.get('bt')
                        },
                        'kp_index': kp_data.get('kp_index')
                    },
                    'predictions': {
                        'aviation': {
                            'hf_blackout_probability': aviation_pred['hf_blackout_probability'],
                            'polar_route_risk': aviation_pred['polar_route_risk']
                        },
                        'telecommunications': {
                            'signal_degradation_percent': telecom_pred['signal_degradation_percent'],
                            'classification': telecom_pred['classification']
                        },
                        'gps': {
                            'positional_drift_cm': gps_pred['positional_drift_cm'],
                            'classification': gps_pred['classification']
                        },
                        'power_grid': {
                            'gic_risk_level': power_grid_pred['gic_risk_level'],
                            'classification': power_grid_pred['classification']
                        },
                        'satellite': {
                            'orbital_drag_risk': satellite_pred['orbital_drag_risk'],
                            'classification': satellite_pred['classification']
                        },
                        'composite': {
                            'score': composite_result['composite_score'],
                            'severity': composite_result['severity']
                        }
                    }
                }
                
                # Broadcast to all clients
                await self.broadcast(update)
                
                # Wait for next update interval (≤ 10 seconds)
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {str(e)}")
                # Continue streaming even if one update fails
                await asyncio.sleep(self.update_interval)
    
    def stop_streaming(self):
        """Stop the streaming loop"""
        self.is_streaming = False
        logger.info("Stopped WebSocket streaming")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket /api/stream endpoint for real-time updates
    
    Establishes persistent connection and streams space weather updates
    
    Features:
    - Connection establishment within 2 seconds
    - Updates pushed at intervals ≤ 10 seconds
    - Automatic reconnection support (client-side)
    - Broadcast to all connected clients simultaneously
    
    Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5
    """
    # Accept connection (with 2-second timeout)
    connected = await manager.connect(websocket)
    
    if not connected:
        logger.error("Failed to establish WebSocket connection within 2 seconds")
        return
    
    # Start streaming if not already running
    if not manager.is_streaming:
        # Start streaming in background task
        asyncio.create_task(manager.start_streaming())
    
    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for messages from client (e.g., ping, reconnection requests)
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                if message.get('type') == 'ping':
                    # Respond to ping
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                elif message.get('type') == 'reconnect':
                    # Client requesting reconnection (already connected)
                    await websocket.send_json({
                        'type': 'reconnect_ack',
                        'timestamp': datetime.utcnow().isoformat(),
                        'message': 'Already connected'
                    })
                
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from client")
            except Exception as e:
                logger.error(f"Error receiving client message: {str(e)}")
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)
