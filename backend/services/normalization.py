"""
Normalization Engine for Space Weather Data
Standardizes data for ML model consumption
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NormalizationEngine:
    """
    Normalizes and encodes space weather data for ML processing
    """
    
    # Min-max ranges for normalization
    NORMALIZATION_RANGES = {
        "solar_wind_speed": (200.0, 1000.0),
        "bz_field": (-100.0, 100.0),
        "kp_index": (0.0, 9.0),
        "proton_flux": (0.0, 1e6),
        "cme_speed": (0.0, 3000.0),
        "density": (0.1, 100.0),
        "temperature": (1e4, 1e7),
    }
    
    # Flare class encoding (higher = more intense)
    FLARE_CLASS_ENCODING = {
        'A': 1,
        'B': 2,
        'C': 3,
        'M': 4,
        'X': 5
    }
    
    def __init__(self):
        self.historical_data: Dict[str, List[float]] = {
            "solar_wind_speed": [],
            "bz_field": [],
            "kp_index": [],
            "proton_flux": [],
            "cme_speed": [],
            "density": [],
            "temperature": []
        }
        self.raw_values_store: Dict[str, Any] = {}
    
    def normalize_numerical(self, value: float, field_name: str) -> float:
        """
        Normalize numerical feature to [0, 1] range using min-max normalization
        
        Args:
            value: Raw numerical value
            field_name: Name of the field being normalized
            
        Returns:
            Normalized value in [0, 1] range
        """
        if field_name not in self.NORMALIZATION_RANGES:
            logger.warning(f"No normalization range defined for {field_name}, returning raw value")
            return value
        
        min_val, max_val = self.NORMALIZATION_RANGES[field_name]
        
        # Clamp value to valid range
        clamped_value = max(min_val, min(max_val, value))
        
        if clamped_value != value:
            logger.debug(f"Value {value} clamped to {clamped_value} for {field_name}")
        
        # Min-max normalization: (x - min) / (max - min)
        normalized = (clamped_value - min_val) / (max_val - min_val)
        
        # Ensure result is in [0, 1]
        normalized = max(0.0, min(1.0, normalized))
        
        logger.debug(f"Normalized {field_name}: {value} -> {normalized:.4f}")
        return normalized
    
    def encode_flare_class(self, flare_class: str) -> int:
        """
        Encode solar flare class as numerical value
        
        Args:
            flare_class: Flare class string (e.g., "X1.5", "M2.3", "C5.0")
            
        Returns:
            Encoded numerical value (1-5 for A-X classes)
        """
        if not flare_class:
            logger.warning("Empty flare class provided, returning 0")
            return 0
        
        # Extract class letter
        class_letter = flare_class[0].upper()
        
        if class_letter not in self.FLARE_CLASS_ENCODING:
            logger.warning(f"Unknown flare class {class_letter}, returning 0")
            return 0
        
        encoded = self.FLARE_CLASS_ENCODING[class_letter]
        
        # Optionally incorporate magnitude for finer granularity
        if len(flare_class) > 1:
            try:
                magnitude = float(flare_class[1:])
                # Add fractional component based on magnitude (0.0-0.9)
                encoded += (magnitude / 10.0)
            except ValueError:
                pass
        
        logger.debug(f"Encoded flare class {flare_class} -> {encoded}")
        return encoded
    
    def impute_missing(self, field_name: str, lookback_hours: int = 6) -> Optional[float]:
        """
        Impute missing values using median of previous N hours
        
        Args:
            field_name: Name of the field with missing data
            lookback_hours: Number of hours to look back for median calculation
            
        Returns:
            Imputed value (median) or None if insufficient data
        """
        if field_name not in self.historical_data:
            logger.warning(f"No historical data for {field_name}")
            return None
        
        historical_values = self.historical_data[field_name]
        
        if not historical_values:
            logger.warning(f"No historical values available for {field_name}")
            return None
        
        # Use last N values (assuming they represent the lookback period)
        # In production, this would filter by actual timestamps
        recent_values = historical_values[-lookback_hours * 12:]  # Assuming 5-min intervals
        
        if not recent_values:
            logger.warning(f"Insufficient recent data for {field_name}")
            return None
        
        # Calculate median
        median_value = np.median(recent_values)
        
        logger.info(f"Imputed missing {field_name} with median: {median_value:.4f}")
        return float(median_value)
    
    def add_to_history(self, field_name: str, value: float):
        """
        Add value to historical data for imputation
        
        Args:
            field_name: Name of the field
            value: Value to add
        """
        if field_name in self.historical_data:
            self.historical_data[field_name].append(value)
            
            # Keep only last 24 hours of data (assuming 5-min intervals = 288 points)
            max_history = 288
            if len(self.historical_data[field_name]) > max_history:
                self.historical_data[field_name] = self.historical_data[field_name][-max_history:]
    
    def preserve_raw_value(self, field_name: str, raw_value: Any, normalized_value: float):
        """
        Store raw value alongside normalized value for audit purposes
        
        Args:
            field_name: Name of the field
            raw_value: Original raw value
            normalized_value: Normalized value
        """
        if field_name not in self.raw_values_store:
            self.raw_values_store[field_name] = []
        
        self.raw_values_store[field_name].append({
            "timestamp": datetime.now().isoformat(),
            "raw": raw_value,
            "normalized": normalized_value
        })
        
        # Keep only last 1000 entries per field
        if len(self.raw_values_store[field_name]) > 1000:
            self.raw_values_store[field_name] = self.raw_values_store[field_name][-1000:]
    
    def normalize_space_weather_data(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalize all space weather data fields
        
        Args:
            data: Raw space weather data
            
        Returns:
            Dictionary of normalized values
        """
        normalized = {}
        
        # Normalize solar wind speed
        if "speed" in data or "solar_wind_speed" in data:
            raw_speed = data.get("speed") or data.get("solar_wind_speed")
            if raw_speed is not None:
                norm_speed = self.normalize_numerical(float(raw_speed), "solar_wind_speed")
                normalized["solar_wind_speed_norm"] = norm_speed
                self.preserve_raw_value("solar_wind_speed", raw_speed, norm_speed)
                self.add_to_history("solar_wind_speed", float(raw_speed))
        
        # Normalize Bz field
        if "bz" in data or "bz_field" in data:
            raw_bz = data.get("bz") or data.get("bz_field")
            if raw_bz is not None:
                norm_bz = self.normalize_numerical(float(raw_bz), "bz_field")
                normalized["bz_field_norm"] = norm_bz
                self.preserve_raw_value("bz_field", raw_bz, norm_bz)
                self.add_to_history("bz_field", float(raw_bz))
        
        # Normalize Kp-index
        if "kp_index" in data:
            raw_kp = data["kp_index"]
            if raw_kp is not None:
                norm_kp = self.normalize_numerical(float(raw_kp), "kp_index")
                normalized["kp_index_norm"] = norm_kp
                self.preserve_raw_value("kp_index", raw_kp, norm_kp)
                self.add_to_history("kp_index", float(raw_kp))
        
        # Normalize proton flux
        if "proton_flux" in data:
            raw_flux = data["proton_flux"]
            if raw_flux is not None:
                norm_flux = self.normalize_numerical(float(raw_flux), "proton_flux")
                normalized["proton_flux_norm"] = norm_flux
                self.preserve_raw_value("proton_flux", raw_flux, norm_flux)
                self.add_to_history("proton_flux", float(raw_flux))
        
        # Normalize CME speed
        if "cme_speed" in data:
            raw_cme = data["cme_speed"]
            if raw_cme is not None:
                norm_cme = self.normalize_numerical(float(raw_cme), "cme_speed")
                normalized["cme_speed_norm"] = norm_cme
                self.preserve_raw_value("cme_speed", raw_cme, norm_cme)
                self.add_to_history("cme_speed", float(raw_cme))
        
        # Encode flare class
        if "flare_class" in data:
            flare_class = data["flare_class"]
            if flare_class:
                encoded = self.encode_flare_class(flare_class)
                normalized["flare_class_encoded"] = encoded
        
        # Handle missing values with imputation
        required_fields = [
            "solar_wind_speed_norm",
            "bz_field_norm",
            "kp_index_norm",
            "proton_flux_norm"
        ]
        
        for field in required_fields:
            if field not in normalized:
                # Try to impute
                base_field = field.replace("_norm", "")
                imputed = self.impute_missing(base_field)
                if imputed is not None:
                    normalized[field] = self.normalize_numerical(imputed, base_field)
                    logger.info(f"Imputed missing {field}")
        
        logger.info(f"Normalized {len(normalized)} fields")
        return normalized
    
    def get_raw_values(self, field_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve raw values for audit purposes
        
        Args:
            field_name: Name of the field
            limit: Maximum number of entries to return
            
        Returns:
            List of raw value records
        """
        if field_name not in self.raw_values_store:
            return []
        
        return self.raw_values_store[field_name][-limit:]
    
    def denormalize(self, normalized_value: float, field_name: str) -> float:
        """
        Convert normalized value back to original scale
        
        Args:
            normalized_value: Normalized value in [0, 1]
            field_name: Name of the field
            
        Returns:
            Denormalized value in original scale
        """
        if field_name not in self.NORMALIZATION_RANGES:
            return normalized_value
        
        min_val, max_val = self.NORMALIZATION_RANGES[field_name]
        
        # Reverse min-max normalization: x = normalized * (max - min) + min
        denormalized = normalized_value * (max_val - min_val) + min_val
        
        return denormalized


# Global instance
normalization_engine = NormalizationEngine()
