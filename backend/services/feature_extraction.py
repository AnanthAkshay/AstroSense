"""
Feature Extraction Engine for Space Weather Data
Transforms raw data into ML-ready feature vectors
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FeatureExtractor:
    """
    Extracts 12-dimensional feature vectors from space weather data
    """
    
    def __init__(self):
        self.historical_measurements: List[Dict[str, Any]] = []
        self.last_flare_time: Optional[datetime] = None
        self.next_cme_arrival: Optional[datetime] = None
    
    def compute_bz_rate_of_change(self, current_bz: float, lookback_minutes: int = 30) -> float:
        """
        Calculate rate of change of Bz magnetic field
        
        Args:
            current_bz: Current Bz value
            lookback_minutes: Time window for rate calculation
            
        Returns:
            Rate of change in nT/hour
        """
        if not self.historical_measurements:
            return 0.0
        
        # Find measurement from lookback_minutes ago
        target_time = datetime.now() - timedelta(minutes=lookback_minutes)
        
        # Find closest historical measurement
        closest_measurement = None
        min_time_diff = timedelta(days=365)
        
        for measurement in self.historical_measurements:
            if "timestamp" in measurement and "bz" in measurement:
                try:
                    meas_time = datetime.fromisoformat(measurement["timestamp"].replace('Z', '+00:00'))
                    time_diff = abs(meas_time - target_time)
                    
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_measurement = measurement
                except (ValueError, AttributeError):
                    continue
        
        if closest_measurement and "bz" in closest_measurement:
            old_bz = float(closest_measurement["bz"])
            time_diff_hours = lookback_minutes / 60.0
            
            if time_diff_hours > 0:
                rate = (current_bz - old_bz) / time_diff_hours
                logger.debug(f"Bz rate of change: {rate:.2f} nT/hour")
                return rate
        
        return 0.0
    
    def compute_wind_speed_variance(self, lookback_hours: int = 3) -> float:
        """
        Calculate variance of solar wind speed over time window
        
        Args:
            lookback_hours: Time window for variance calculation
            
        Returns:
            Variance of wind speed
        """
        if len(self.historical_measurements) < 2:
            return 0.0
        
        # Extract wind speeds from recent measurements
        speeds = []
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        
        for measurement in self.historical_measurements:
            if "timestamp" in measurement and "speed" in measurement:
                try:
                    meas_time = datetime.fromisoformat(measurement["timestamp"].replace('Z', '+00:00'))
                    if meas_time >= cutoff_time:
                        speeds.append(float(measurement["speed"]))
                except (ValueError, AttributeError, TypeError):
                    continue
        
        if len(speeds) >= 2:
            variance = float(np.var(speeds))
            logger.debug(f"Wind speed variance: {variance:.2f}")
            return variance
        
        return 0.0
    
    def compute_time_since_last_flare(self) -> float:
        """
        Calculate time since last solar flare in hours
        
        Returns:
            Hours since last flare (capped at 168 hours = 1 week)
        """
        if self.last_flare_time is None:
            return 168.0  # Default to 1 week if no flare recorded
        
        time_diff = datetime.now() - self.last_flare_time
        hours = time_diff.total_seconds() / 3600.0
        
        # Cap at 1 week
        hours = min(hours, 168.0)
        
        logger.debug(f"Time since last flare: {hours:.2f} hours")
        return hours
    
    def compute_cme_arrival_proximity(self) -> float:
        """
        Calculate proximity to next CME arrival (0 = far, 1 = imminent)
        
        Returns:
            Normalized proximity value [0, 1]
        """
        if self.next_cme_arrival is None:
            return 0.0  # No CME expected
        
        time_until = self.next_cme_arrival - datetime.now()
        hours_until = time_until.total_seconds() / 3600.0
        
        if hours_until <= 0:
            return 1.0  # CME has arrived or passed
        
        # Normalize: 0 hours = 1.0, 72 hours = 0.0
        max_hours = 72.0
        proximity = 1.0 - min(hours_until / max_hours, 1.0)
        
        logger.debug(f"CME arrival proximity: {proximity:.4f} ({hours_until:.1f} hours until)")
        return proximity
    
    def compute_geomagnetic_latitude_factor(self, latitude: float = 45.0) -> float:
        """
        Calculate geomagnetic latitude factor (higher latitudes more affected)
        
        Args:
            latitude: Geographic latitude in degrees
            
        Returns:
            Normalized latitude factor [0, 1]
        """
        # Convert to geomagnetic latitude (simplified)
        # Higher latitudes (closer to poles) are more affected by space weather
        abs_latitude = abs(latitude)
        
        # Normalize: 0° = 0.0, 90° = 1.0
        factor = abs_latitude / 90.0
        
        logger.debug(f"Geomagnetic latitude factor: {factor:.4f} for {latitude}°")
        return factor
    
    def compute_local_time_factor(self, longitude: float = 0.0) -> float:
        """
        Calculate local time factor (midnight sector more vulnerable)
        
        Args:
            longitude: Geographic longitude in degrees
            
        Returns:
            Local time factor [0, 1] where 1 = midnight sector
        """
        # Calculate local time from longitude and UTC time
        current_utc = datetime.utcnow()
        hours_offset = longitude / 15.0  # 15° per hour
        local_hour = (current_utc.hour + hours_offset) % 24
        
        # Midnight sector (22:00 - 02:00) is most vulnerable
        # Peak vulnerability at midnight (0:00)
        if 22 <= local_hour or local_hour <= 2:
            # Calculate distance from midnight
            if local_hour >= 22:
                distance_from_midnight = min(24 - local_hour, local_hour - 22)
            else:
                distance_from_midnight = local_hour
            
            # Closer to midnight = higher factor
            factor = 1.0 - (distance_from_midnight / 2.0)
        else:
            # Daytime - lower vulnerability
            factor = 0.2
        
        logger.debug(f"Local time factor: {factor:.4f} for {local_hour:.1f}:00 local time")
        return factor
    
    def extract_features(self, raw_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract 12-dimensional feature vector from raw space weather data
        
        Args:
            raw_data: Dictionary containing normalized space weather measurements
            
        Returns:
            12-dimensional numpy array of features
        """
        features = []
        
        # Feature 1: Solar wind speed (normalized)
        solar_wind_speed_norm = raw_data.get("solar_wind_speed_norm", 0.5)
        features.append(solar_wind_speed_norm)
        
        # Feature 2: Bz magnetic field (normalized)
        bz_field_norm = raw_data.get("bz_field_norm", 0.5)
        features.append(bz_field_norm)
        
        # Feature 3: Kp-index (normalized)
        kp_index_norm = raw_data.get("kp_index_norm", 0.3)
        features.append(kp_index_norm)
        
        # Feature 4: Proton flux (normalized)
        proton_flux_norm = raw_data.get("proton_flux_norm", 0.1)
        features.append(proton_flux_norm)
        
        # Feature 5: CME speed (normalized)
        cme_speed_norm = raw_data.get("cme_speed_norm", 0.0)
        features.append(cme_speed_norm)
        
        # Feature 6: Flare class (encoded)
        flare_class_encoded = raw_data.get("flare_class_encoded", 0.0)
        # Normalize to [0, 1] range (max encoding is 5.9 for X9.9)
        flare_class_norm = min(flare_class_encoded / 6.0, 1.0)
        features.append(flare_class_norm)
        
        # Feature 7: Bz rate of change
        current_bz = raw_data.get("bz", 0.0)
        bz_rate = self.compute_bz_rate_of_change(float(current_bz))
        # Normalize rate: -50 to +50 nT/hour -> [0, 1]
        bz_rate_norm = (bz_rate + 50.0) / 100.0
        bz_rate_norm = max(0.0, min(1.0, bz_rate_norm))
        features.append(bz_rate_norm)
        
        # Feature 8: Wind speed variance
        wind_variance = self.compute_wind_speed_variance()
        # Normalize variance: 0 to 10000 -> [0, 1]
        wind_variance_norm = min(wind_variance / 10000.0, 1.0)
        features.append(wind_variance_norm)
        
        # Feature 9: Time since last flare
        time_since_flare = self.compute_time_since_last_flare()
        # Normalize: 0 to 168 hours -> [0, 1]
        time_since_flare_norm = time_since_flare / 168.0
        features.append(time_since_flare_norm)
        
        # Feature 10: CME arrival proximity
        cme_proximity = self.compute_cme_arrival_proximity()
        features.append(cme_proximity)
        
        # Feature 11: Geomagnetic latitude factor
        latitude = raw_data.get("latitude", 45.0)
        lat_factor = self.compute_geomagnetic_latitude_factor(float(latitude))
        features.append(lat_factor)
        
        # Feature 12: Local time factor
        longitude = raw_data.get("longitude", 0.0)
        time_factor = self.compute_local_time_factor(float(longitude))
        features.append(time_factor)
        
        feature_vector = np.array(features, dtype=np.float32)
        
        logger.info(f"Extracted {len(feature_vector)}-dimensional feature vector")
        logger.debug(f"Feature vector: {feature_vector}")
        
        return feature_vector
    
    def update_historical_data(self, measurement: Dict[str, Any]):
        """
        Add measurement to historical data for derived feature calculation
        
        Args:
            measurement: Space weather measurement with timestamp
        """
        # Add timestamp if not present
        if "timestamp" not in measurement:
            measurement["timestamp"] = datetime.now().isoformat()
        
        self.historical_measurements.append(measurement)
        
        # Keep only last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.historical_measurements = [
            m for m in self.historical_measurements
            if datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')) >= cutoff_time
        ]
        
        logger.debug(f"Historical measurements: {len(self.historical_measurements)} records")
    
    def update_flare_time(self, flare_time: datetime):
        """
        Update the last solar flare detection time
        
        Args:
            flare_time: Datetime of flare detection
        """
        self.last_flare_time = flare_time
        logger.info(f"Updated last flare time: {flare_time.isoformat()}")
    
    def update_cme_arrival(self, arrival_time: datetime):
        """
        Update the next CME arrival prediction
        
        Args:
            arrival_time: Predicted CME arrival datetime
        """
        self.next_cme_arrival = arrival_time
        logger.info(f"Updated CME arrival prediction: {arrival_time.isoformat()}")
    
    def get_feature_names(self) -> List[str]:
        """
        Get names of all features in the feature vector
        
        Returns:
            List of feature names
        """
        return [
            "solar_wind_speed_norm",
            "bz_field_norm",
            "kp_index_norm",
            "proton_flux_norm",
            "cme_speed_norm",
            "flare_class_norm",
            "bz_rate_of_change",
            "wind_speed_variance",
            "time_since_last_flare",
            "cme_arrival_proximity",
            "geomagnetic_latitude_factor",
            "local_time_factor"
        ]


# Global instance
feature_extractor = FeatureExtractor()
