"""
Alert Management System for AstroSense
Generates, prioritizes, and manages space weather alerts
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timezone, timedelta
import uuid
import time
from collections import defaultdict
from models.alert import Alert, FlashAlert, ImpactForecast, AlertType, AlertSeverity
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Constants for forecast merging
MERGE_WINDOW = 30 * 60  # 30 minutes in seconds

# Global storage for active forecasts (in production, use Redis or database)
_active_forecasts = {}  # key -> {"payload": dict, "created_at": timestamp}


def validate_alert_payload(payload: Dict[str, Any]) -> bool:
    """
    Validate alert payload has all required fields with correct types
    
    Args:
        payload: Alert payload dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If payload is invalid
    """
    required_fields = {
        "alert_id": str,
        "timestamp": str,  # ISO 8601
        "severity": str,
        "affected_sectors": list,
        "mitigation_recommendations": list,
    }
    
    # For forecasts, also require confidence interval fields
    if payload.get("alert_type") == "FORECAST":
        required_fields.update({
            "confidence_percent": (int, float),
            "arrival_time_lower": str,
            "arrival_time_upper": str,
        })
    
    missing = []
    wrong_types = []
    
    for field, expected_type in required_fields.items():
        if field not in payload:
            missing.append(field)
        else:
            if not isinstance(payload[field], expected_type):
                wrong_types.append((field, type(payload[field]).__name__, expected_type))
    
    if missing or wrong_types:
        raise ValueError(f"Alert payload invalid. Missing: {missing}, Wrong types: {wrong_types}")
    
    # Validate timestamp format
    try:
        datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
    except Exception as e:
        raise ValueError("timestamp must be ISO8601") from e
    
    return True


def forecast_key(payload: Dict[str, Any]) -> str:
    """
    Generate canonical key for forecast deduplication
    
    Args:
        payload: Forecast payload
        
    Returns:
        Canonical key string
    """
    event_type = payload.get("alert_type", "FORECAST")
    
    # Round timestamp to nearest 5 minutes for grouping
    timestamp_str = payload.get("timestamp", "")
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        rounded = int(ts.timestamp() // 300)  # 300s = 5min bucket
    except:
        rounded = 0
    
    location = payload.get("location", "global")
    return f"{event_type}|{rounded}|{location}"


def merge_forecasts(existing: Dict[str, Any], new_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two forecast payloads using weighted average
    
    Args:
        existing: Existing forecast data
        new_payload: New forecast payload
        
    Returns:
        Merged forecast data
    """
    ex_payload = existing["payload"]
    
    # Weight by confidence scores
    w1 = ex_payload.get("confidence_percent", 50.0)
    w2 = new_payload.get("confidence_percent", 50.0)
    total_weight = w1 + w2
    
    if total_weight > 0:
        # Merge confidence intervals conservatively
        merged_confidence = min(100.0, (w1 + w2) / 2)  # Average confidence
        
        # Widen confidence interval to be conservative
        ex_lower = ex_payload.get("arrival_time_lower", "")
        ex_upper = ex_payload.get("arrival_time_upper", "")
        new_lower = new_payload.get("arrival_time_lower", "")
        new_upper = new_payload.get("arrival_time_upper", "")
        
        try:
            ex_lower_dt = datetime.fromisoformat(ex_lower.replace("Z", "+00:00"))
            ex_upper_dt = datetime.fromisoformat(ex_upper.replace("Z", "+00:00"))
            new_lower_dt = datetime.fromisoformat(new_lower.replace("Z", "+00:00"))
            new_upper_dt = datetime.fromisoformat(new_upper.replace("Z", "+00:00"))
            
            merged_lower = min(ex_lower_dt, new_lower_dt)
            merged_upper = max(ex_upper_dt, new_upper_dt)
            
            ex_payload.update({
                "confidence_percent": merged_confidence,
                "arrival_time_lower": merged_lower.isoformat().replace("+00:00", "Z"),
                "arrival_time_upper": merged_upper.isoformat().replace("+00:00", "Z"),
            })
        except:
            # If datetime parsing fails, keep existing values
            pass
    
    existing["created_at"] = time.time()
    return existing


def handle_new_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle new forecast with deduplication and merging
    
    Args:
        payload: New forecast payload
        
    Returns:
        Final payload (merged or original)
    """
    key = forecast_key(payload)
    now = time.time()
    
    if key in _active_forecasts:
        existing = _active_forecasts[key]
        if now - existing["created_at"] <= MERGE_WINDOW:
            # Merge with existing forecast
            merged = merge_forecasts(existing, payload)
            _active_forecasts[key] = merged
            logger.info(f"Merged forecast with existing key: {key}")
            return merged["payload"]
    
    # Store new forecast
    _active_forecasts[key] = {"payload": payload, "created_at": now}
    logger.info(f"Stored new forecast with key: {key}")
    return payload


class AlertManager:
    """
    Manages space weather alerts including flash alerts and impact forecasts
    
    Features:
    - Generate flash alerts for X-class flares (< 10 seconds)
    - Create impact forecasts for CMEs with confidence intervals
    - Prioritize alerts by severity then chronological order
    - Implement 2-hour alert expiration and history archival
    - Include mitigation recommendations in alerts
    """
    
    def __init__(self):
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.alert_expiration_hours = 2
    
    def generate_flash_alert(
        self,
        flare_class: str,
        detection_time: datetime,
        space_weather_data: Dict[str, Any],
        generation_start_time: Optional[datetime] = None
    ) -> FlashAlert:
        """
        Generate flash alert for X-class solar flare
        Must complete within 10 seconds of detection
        
        Args:
            flare_class: Solar flare classification (e.g., 'X2.5')
            detection_time: Time when flare was detected
            space_weather_data: Current space weather measurements
            generation_start_time: Optional start time for performance tracking
            
        Returns:
            FlashAlert object
        """
        if generation_start_time is None:
            generation_start_time = datetime.now(timezone.utc)
        
        # Determine severity based on flare class
        severity = self._determine_flare_severity(flare_class)
        
        # Identify affected sectors
        affected_sectors = self._identify_affected_sectors_for_flare(
            flare_class, space_weather_data
        )
        
        # Generate alert ID
        alert_id = str(uuid.uuid4())
        
        # Create timestamps
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=self.alert_expiration_hours)
        
        # Create title and description
        title = f"FLASH ALERT: {flare_class} Solar Flare Detected"
        description = (
            f"An {flare_class} solar flare was detected at {detection_time.isoformat()}. "
            f"Immediate radio blackout effects are expected. "
            f"Affected sectors: {', '.join(affected_sectors)}."
        )
        
        # Get mitigation recommendations
        mitigation = self._get_flare_mitigation_recommendations(
            flare_class, affected_sectors
        )
        
        # Create flash alert
        flash_alert = FlashAlert(
            alert_id=alert_id,
            severity=severity,
            title=title,
            description=description,
            affected_sectors=affected_sectors,
            created_at=created_at,
            expires_at=expires_at,
            mitigation_recommendations=mitigation,
            flare_class=flare_class,
            detection_time=detection_time
        )
        
        # Add to active alerts
        self.active_alerts.append(flash_alert)
        
        # Log generation time
        generation_time = (datetime.now(timezone.utc) - generation_start_time).total_seconds()
        logger.info(f"Flash alert generated in {generation_time:.3f}s for {flare_class} flare")
        
        if generation_time > 10.0:
            logger.warning(f"Flash alert generation exceeded 10s threshold: {generation_time:.3f}s")
        
        return flash_alert
    
    def create_impact_forecast(
        self,
        cme_data: Dict[str, Any],
        space_weather_data: Dict[str, Any],
        sector_predictions: Dict[str, Any]
    ) -> ImpactForecast:
        """
        Create impact forecast for CME with confidence intervals
        
        Args:
            cme_data: CME event data including speed and detection time
            space_weather_data: Current space weather measurements
            sector_predictions: Predicted impacts for each sector
            
        Returns:
            ImpactForecast object
        """
        # Calculate arrival time with confidence interval
        arrival_time_lower, arrival_time_upper, confidence = self._calculate_arrival_confidence(
            cme_data
        )
        
        # Predict Kp-index
        predicted_kp = self._predict_kp_index(cme_data, space_weather_data)
        
        # Determine severity
        severity = self._determine_forecast_severity(predicted_kp, sector_predictions)
        
        # Identify affected sectors
        affected_sectors = self._identify_affected_sectors_from_predictions(
            sector_predictions
        )
        
        # Generate alert ID
        alert_id = str(uuid.uuid4())
        
        # Create timestamps
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(hours=self.alert_expiration_hours)
        
        # Create title and description
        cme_speed = cme_data.get('cme_speed', 0)
        title = f"CME IMPACT FORECAST: Arrival Expected in {self._format_time_until(arrival_time_lower)}"
        description = (
            f"A CME traveling at {cme_speed:.0f} km/s is expected to arrive between "
            f"{arrival_time_lower.isoformat()} and {arrival_time_upper.isoformat()} "
            f"(confidence: {confidence:.0f}%). "
            f"Predicted Kp-index: {predicted_kp:.1f}. "
            f"Affected sectors: {', '.join(affected_sectors)}."
        )
        
        # Get mitigation recommendations
        mitigation = self._get_forecast_mitigation_recommendations(
            predicted_kp, affected_sectors, sector_predictions
        )
        
        # Create forecast payload for validation and merging
        forecast_payload = {
            "alert_id": alert_id,
            "alert_type": "FORECAST",
            "timestamp": created_at.isoformat().replace("+00:00", "Z"),
            "severity": severity.value,
            "affected_sectors": affected_sectors,
            "mitigation_recommendations": mitigation,
            "confidence_percent": confidence,
            "arrival_time_lower": arrival_time_lower.isoformat().replace("+00:00", "Z"),
            "arrival_time_upper": arrival_time_upper.isoformat().replace("+00:00", "Z"),
            "predicted_kp_index": predicted_kp,
            "sector_impacts": sector_predictions
        }
        
        # Validate payload
        validate_alert_payload(forecast_payload)
        
        # Handle deduplication and merging
        final_payload = handle_new_forecast(forecast_payload)
        
        # Create impact forecast from final payload
        forecast = ImpactForecast(
            alert_id=final_payload["alert_id"],
            severity=AlertSeverity(final_payload["severity"]),
            title=title,
            description=description,
            affected_sectors=final_payload["affected_sectors"],
            created_at=datetime.fromisoformat(final_payload["timestamp"].replace("Z", "+00:00")),
            expires_at=expires_at,
            mitigation_recommendations=final_payload["mitigation_recommendations"],
            predicted_kp_index=final_payload["predicted_kp_index"],
            arrival_time_lower=datetime.fromisoformat(final_payload["arrival_time_lower"].replace("Z", "+00:00")),
            arrival_time_upper=datetime.fromisoformat(final_payload["arrival_time_upper"].replace("Z", "+00:00")),
            confidence_percent=final_payload["confidence_percent"],
            sector_impacts=final_payload["sector_impacts"]
        )
        
        # Add to active alerts
        self.active_alerts.append(forecast)
        
        logger.info(f"Impact forecast created: CME arrival {final_payload['arrival_time_lower']} "
                   f"(confidence: {final_payload['confidence_percent']:.0f}%)")
        
        return forecast
    
    def prioritize_alerts(self) -> List[Alert]:
        """
        Prioritize alerts by severity then chronological order
        
        Returns:
            Sorted list of active alerts
        """
        # Define severity order (higher priority first)
        severity_order = {
            AlertSeverity.CRITICAL: 5,
            AlertSeverity.HIGH: 4,
            AlertSeverity.WARNING: 3,
            AlertSeverity.MODERATE: 2,
            AlertSeverity.LOW: 1
        }
        
        # Sort by severity (descending) then by creation time (ascending)
        prioritized = sorted(
            self.active_alerts,
            key=lambda alert: (
                -severity_order.get(alert.severity, 0),  # Negative for descending
                alert.created_at  # Ascending (oldest first within same severity)
            )
        )
        
        logger.debug(f"Prioritized {len(prioritized)} active alerts")
        
        return prioritized
    
    def expire_old_alerts(self, current_time: Optional[datetime] = None) -> int:
        """
        Move expired alerts to history (2-hour expiration)
        
        Args:
            current_time: Optional current time (defaults to now)
            
        Returns:
            Number of alerts expired
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        expired_alerts = []
        active_alerts = []
        
        for alert in self.active_alerts:
            if alert.is_expired(current_time):
                expired_alerts.append(alert)
            else:
                active_alerts.append(alert)
        
        # Move expired alerts to history
        self.alert_history.extend(expired_alerts)
        self.active_alerts = active_alerts
        
        if expired_alerts:
            logger.info(f"Expired {len(expired_alerts)} alerts, moved to history")
        
        return len(expired_alerts)
    
    def get_active_alerts(self, prioritized: bool = True) -> List[Alert]:
        """
        Get all active alerts
        
        Args:
            prioritized: Whether to return prioritized list
            
        Returns:
            List of active alerts
        """
        # First expire old alerts
        self.expire_old_alerts()
        
        if prioritized:
            return self.prioritize_alerts()
        else:
            return self.active_alerts.copy()
    
    def get_alert_history(self) -> List[Alert]:
        """
        Get alert history
        
        Returns:
            List of expired alerts
        """
        return self.alert_history.copy()
    
    def _determine_flare_severity(self, flare_class: str) -> AlertSeverity:
        """Determine severity based on flare class"""
        if not flare_class:
            return AlertSeverity.LOW
        
        class_letter = flare_class[0].upper()
        
        if class_letter == 'X':
            # X-class flares are critical
            try:
                magnitude = float(flare_class[1:])
                if magnitude >= 10:
                    return AlertSeverity.CRITICAL
                else:
                    return AlertSeverity.HIGH
            except (ValueError, IndexError):
                return AlertSeverity.HIGH
        elif class_letter == 'M':
            return AlertSeverity.WARNING
        elif class_letter == 'C':
            return AlertSeverity.MODERATE
        else:
            return AlertSeverity.LOW
    
    def _identify_affected_sectors_for_flare(
        self,
        flare_class: str,
        space_weather_data: Dict[str, Any]
    ) -> List[str]:
        """Identify sectors affected by solar flare"""
        affected = []
        
        # X-class and M-class flares affect HF communications
        if flare_class and flare_class[0].upper() in ['X', 'M']:
            affected.extend(['aviation', 'telecommunications'])
        
        # High Kp-index affects GPS and power grids
        kp_index = space_weather_data.get('kp_index', 0)
        if kp_index >= 5:
            affected.extend(['gps', 'power_grid'])
        
        # Satellites affected by radiation
        if flare_class and flare_class[0].upper() == 'X':
            affected.append('satellite')
        
        return list(set(affected))  # Remove duplicates
    
    def _get_flare_mitigation_recommendations(
        self,
        flare_class: str,
        affected_sectors: List[str]
    ) -> List[str]:
        """Get mitigation recommendations for flare event"""
        recommendations = []
        
        if 'aviation' in affected_sectors:
            recommendations.extend([
                'Prepare backup communication systems for aircraft',
                'Brief flight crews on potential HF radio disruptions',
                'Monitor space weather updates closely'
            ])
        
        if 'telecommunications' in affected_sectors:
            recommendations.extend([
                'Activate backup communication systems',
                'Notify customers of potential service disruptions'
            ])
        
        if 'gps' in affected_sectors:
            recommendations.append('Warn users of potential GPS accuracy degradation')
        
        if 'power_grid' in affected_sectors:
            recommendations.extend([
                'Monitor transformer temperatures',
                'Prepare for potential voltage instabilities'
            ])
        
        if 'satellite' in affected_sectors:
            recommendations.extend([
                'Monitor satellite health closely',
                'Prepare for increased radiation exposure'
            ])
        
        return recommendations
    
    def _calculate_arrival_confidence(
        self,
        cme_data: Dict[str, Any]
    ) -> Tuple[datetime, datetime, float]:
        """
        Calculate CME arrival time with confidence interval
        
        Returns:
            Tuple of (lower_bound, upper_bound, confidence_percent)
        """
        cme_speed = cme_data.get('cme_speed', 500)
        detection_time = cme_data.get('detection_time', datetime.now(timezone.utc))
        
        # Ensure detection_time is timezone-aware
        if detection_time.tzinfo is None:
            detection_time = detection_time.replace(tzinfo=timezone.utc)
        
        # Distance to Earth: ~150 million km
        distance_km = 150_000_000
        
        # Calculate nominal arrival time
        travel_time_hours = distance_km / cme_speed / 3600
        
        # Cap at 7 days maximum
        travel_time_hours = min(travel_time_hours, 168)
        
        nominal_arrival = detection_time + timedelta(hours=travel_time_hours)
        
        # Confidence interval: ±20% of travel time
        uncertainty_hours = travel_time_hours * 0.2
        arrival_lower = nominal_arrival - timedelta(hours=uncertainty_hours)
        arrival_upper = nominal_arrival + timedelta(hours=uncertainty_hours)
        
        # Confidence based on CME speed (faster = more confident)
        if cme_speed > 1000:
            confidence = 85.0
        elif cme_speed > 700:
            confidence = 75.0
        elif cme_speed > 500:
            confidence = 65.0
        else:
            confidence = 50.0
        
        return arrival_lower, arrival_upper, confidence
    
    def _predict_kp_index(
        self,
        cme_data: Dict[str, Any],
        space_weather_data: Dict[str, Any]
    ) -> float:
        """Predict Kp-index from CME and current conditions"""
        cme_speed = cme_data.get('cme_speed', 500)
        current_kp = space_weather_data.get('kp_index', 3.0)
        bz = space_weather_data.get('bz', 0.0)
        
        # Base prediction on CME speed
        if cme_speed > 1500:
            predicted_kp = 8.0
        elif cme_speed > 1000:
            predicted_kp = 7.0
        elif cme_speed > 700:
            predicted_kp = 6.0
        elif cme_speed > 500:
            predicted_kp = 5.0
        else:
            predicted_kp = 4.0
        
        # Adjust for negative Bz (increases storm intensity)
        if bz < -10:
            predicted_kp = min(predicted_kp + 1.0, 9.0)
        
        # Blend with current conditions
        predicted_kp = (predicted_kp * 0.7) + (current_kp * 0.3)
        
        return min(predicted_kp, 9.0)
    
    def _determine_forecast_severity(
        self,
        predicted_kp: float,
        sector_predictions: Dict[str, Any]
    ) -> AlertSeverity:
        """Determine severity for impact forecast"""
        # Check for critical conditions
        if predicted_kp >= 8.0:
            return AlertSeverity.CRITICAL
        
        # Check sector predictions for high risks
        high_risk_count = 0
        
        aviation = sector_predictions.get('aviation', {})
        if aviation.get('hf_blackout_probability', 0) > 80:
            high_risk_count += 1
        
        telecom = sector_predictions.get('telecom', {})
        if telecom.get('signal_degradation_percent', 0) > 70:
            high_risk_count += 1
        
        gps = sector_predictions.get('gps', {})
        if gps.get('positional_drift_cm', 0) > 250:
            high_risk_count += 1
        
        power_grid = sector_predictions.get('power_grid', {})
        if power_grid.get('gic_risk_level', 0) >= 8:
            high_risk_count += 1
        
        if high_risk_count >= 3:
            return AlertSeverity.CRITICAL
        elif high_risk_count >= 2:
            return AlertSeverity.HIGH
        elif predicted_kp >= 6.0:
            return AlertSeverity.WARNING
        elif predicted_kp >= 4.0:
            return AlertSeverity.MODERATE
        else:
            return AlertSeverity.LOW
    
    def _identify_affected_sectors_from_predictions(
        self,
        sector_predictions: Dict[str, Any]
    ) -> List[str]:
        """Identify affected sectors from predictions"""
        affected = []
        
        aviation = sector_predictions.get('aviation', {})
        if aviation.get('hf_blackout_probability', 0) > 30:
            affected.append('aviation')
        
        telecom = sector_predictions.get('telecom', {})
        if telecom.get('signal_degradation_percent', 0) > 20:
            affected.append('telecommunications')
        
        gps = sector_predictions.get('gps', {})
        if gps.get('positional_drift_cm', 0) > 30:
            affected.append('gps')
        
        power_grid = sector_predictions.get('power_grid', {})
        if power_grid.get('gic_risk_level', 0) >= 5:
            affected.append('power_grid')
        
        satellite = sector_predictions.get('satellite', {})
        if satellite.get('orbital_drag_risk', 0) >= 5:
            affected.append('satellite')
        
        return affected
    
    def _get_forecast_mitigation_recommendations(
        self,
        predicted_kp: float,
        affected_sectors: List[str],
        sector_predictions: Dict[str, Any]
    ) -> List[str]:
        """Get mitigation recommendations for forecast"""
        recommendations = []
        
        # General recommendations for high Kp
        if predicted_kp >= 7.0:
            recommendations.append('Activate emergency response protocols across all sectors')
        
        # Sector-specific recommendations
        if 'aviation' in affected_sectors:
            recommendations.extend([
                'Consider rerouting polar flights to lower latitudes',
                'Prepare backup communication systems'
            ])
        
        if 'telecommunications' in affected_sectors:
            recommendations.extend([
                'Prepare redundant satellite links',
                'Increase monitoring of network performance'
            ])
        
        if 'gps' in affected_sectors:
            recommendations.extend([
                'Use differential GPS corrections where available',
                'Increase position uncertainty margins'
            ])
        
        if 'power_grid' in affected_sectors:
            recommendations.extend([
                'Activate transformer protection systems',
                'Reduce grid loading where possible'
            ])
        
        if 'satellite' in affected_sectors:
            recommendations.extend([
                'Consider orbit adjustment maneuvers',
                'Prepare for increased fuel consumption'
            ])
        
        return recommendations
    
    def _format_time_until(self, future_time: datetime) -> str:
        """Format time until future event"""
        # Ensure future_time is timezone-aware
        if future_time.tzinfo is None:
            future_time = future_time.replace(tzinfo=timezone.utc)
        
        delta = future_time - datetime.now(timezone.utc)
        hours = delta.total_seconds() / 3600
        
        if hours < 1:
            return "less than 1 hour"
        elif hours < 24:
            return f"{int(hours)} hours"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            if remaining_hours > 0:
                return f"{days} days {remaining_hours} hours"
            else:
                return f"{days} days"


# Global instance
alert_manager = AlertManager()
