"""
Validation Engine for Space Weather Data
Ensures data quality and completeness before processing
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass


class ValidationEngine:
    """
    Validates space weather data for completeness and correctness
    """
    
    # Define physically plausible ranges for space weather parameters
    VALID_RANGES = {
        "solar_wind_speed": (200.0, 1000.0),  # km/s
        "bz_field": (-100.0, 100.0),  # nT (nanoteslas)
        "kp_index": (0.0, 9.0),  # Kp scale
        "proton_flux": (0.0, 1e6),  # particles/cm²/s/sr
        "cme_speed": (0.0, 3000.0),  # km/s
        "density": (0.1, 100.0),  # particles/cm³
        "temperature": (1e4, 1e7),  # Kelvin
    }
    
    # Required fields for different data types
    REQUIRED_FIELDS = {
        "space_weather_data": ["timestamp", "source"],
        "solar_wind": ["timestamp", "speed", "source"],
        "magnetic_field": ["timestamp", "bz", "source"],
        "kp_index": ["timestamp", "kp_index", "source"],
        "cme_event": ["event_id", "detection_time", "source"],
        "solar_flare": ["flare_id", "detection_time", "flare_class", "source"]
    }
    
    def __init__(self):
        self.validation_failures: List[Dict[str, Any]] = []
        self.data_quality_metrics = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "completeness_percentage": 100.0
        }
    
    def validate_completeness(self, data: Dict[str, Any], data_type: str = "space_weather_data") -> bool:
        """
        Verify that all required fields are present in the data
        
        Args:
            data: Dictionary containing space weather data
            data_type: Type of data being validated
            
        Returns:
            True if all required fields are present, False otherwise
        """
        required_fields = self.REQUIRED_FIELDS.get(data_type, self.REQUIRED_FIELDS["space_weather_data"])
        
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Missing required fields for {data_type}: {missing_fields}"
            logger.warning(error_msg)
            self._log_validation_failure(data, "completeness", error_msg)
            return False
        
        logger.debug(f"Completeness validation passed for {data_type}")
        return True
    
    def validate_ranges(self, data: Dict[str, Any]) -> bool:
        """
        Check that numerical values are within physically plausible ranges
        
        Args:
            data: Dictionary containing space weather measurements
            
        Returns:
            True if all values are within valid ranges, False otherwise
        """
        out_of_range = []
        
        for field, (min_val, max_val) in self.VALID_RANGES.items():
            if field in data and data[field] is not None:
                value = data[field]
                
                # Handle different field name variations
                if field == "bz_field" and "bz" in data:
                    value = data["bz"]
                elif field == "solar_wind_speed" and "speed" in data:
                    value = data["speed"]
                
                try:
                    value = float(value)
                    if not (min_val <= value <= max_val):
                        out_of_range.append({
                            "field": field,
                            "value": value,
                            "valid_range": (min_val, max_val)
                        })
                except (ValueError, TypeError) as e:
                    error_msg = f"Invalid numeric value for {field}: {value}"
                    logger.warning(error_msg)
                    self._log_validation_failure(data, "type_error", error_msg)
                    return False
        
        if out_of_range:
            error_msg = f"Values out of valid range: {out_of_range}"
            logger.warning(error_msg)
            self._log_validation_failure(data, "range", error_msg)
            return False
        
        logger.debug("Range validation passed")
        return True
    
    def validate_timestamps(self, data_records: List[Dict[str, Any]]) -> bool:
        """
        Verify that timestamps are in chronological order
        
        Args:
            data_records: List of data records with timestamps
            
        Returns:
            True if timestamps are chronological, False otherwise
        """
        if len(data_records) < 2:
            return True  # Single record or empty list is trivially ordered
        
        timestamps = []
        for record in data_records:
            if "timestamp" not in record:
                logger.warning("Record missing timestamp field")
                return False
            
            try:
                # Parse timestamp (handle various formats)
                ts_str = record["timestamp"]
                if isinstance(ts_str, datetime):
                    ts = ts_str
                else:
                    # Try ISO format first
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                timestamps.append(ts)
            except (ValueError, AttributeError) as e:
                error_msg = f"Invalid timestamp format: {record.get('timestamp')}"
                logger.warning(error_msg)
                self._log_validation_failure(record, "timestamp_format", error_msg)
                return False
        
        # Check chronological order
        for i in range(1, len(timestamps)):
            if timestamps[i] < timestamps[i-1]:
                error_msg = f"Timestamps not in chronological order at index {i}"
                logger.warning(error_msg)
                self._log_validation_failure(
                    {"index": i, "current": timestamps[i], "previous": timestamps[i-1]},
                    "chronology",
                    error_msg
                )
                return False
        
        logger.debug(f"Timestamp chronology validation passed for {len(timestamps)} records")
        return True
    
    def validate_flare_class(self, flare_class: str) -> bool:
        """
        Validate solar flare classification
        
        Args:
            flare_class: Flare class string (e.g., "X1.5", "M2.3", "C5.0")
            
        Returns:
            True if valid flare class, False otherwise
        """
        if not flare_class:
            return False
        
        # Valid flare classes: X, M, C, B, A (in order of intensity)
        valid_classes = ['X', 'M', 'C', 'B', 'A']
        
        # Extract the class letter
        class_letter = flare_class[0].upper()
        
        if class_letter not in valid_classes:
            logger.warning(f"Invalid flare class: {flare_class}")
            return False
        
        # Optionally validate the magnitude (if present)
        if len(flare_class) > 1:
            try:
                magnitude = float(flare_class[1:])
                if magnitude < 0 or magnitude >= 10:
                    logger.warning(f"Invalid flare magnitude: {magnitude}")
                    return False
            except ValueError:
                logger.warning(f"Invalid flare class format: {flare_class}")
                return False
        
        return True
    
    def validate_record(self, data: Dict[str, Any], data_type: str = "space_weather_data") -> bool:
        """
        Perform complete validation on a single data record
        
        Args:
            data: Data record to validate
            data_type: Type of data being validated
            
        Returns:
            True if all validations pass, False otherwise
        """
        self.data_quality_metrics["total_records"] += 1
        
        # Check completeness
        if not self.validate_completeness(data, data_type):
            self.data_quality_metrics["invalid_records"] += 1
            return False
        
        # Check ranges for numerical fields
        if not self.validate_ranges(data):
            self.data_quality_metrics["invalid_records"] += 1
            return False
        
        # Special validation for solar flares
        if data_type == "solar_flare" and "flare_class" in data:
            if not self.validate_flare_class(data["flare_class"]):
                self.data_quality_metrics["invalid_records"] += 1
                return False
        
        self.data_quality_metrics["valid_records"] += 1
        return True
    
    def _log_validation_failure(self, data: Dict[str, Any], failure_type: str, message: str):
        """
        Log validation failure with details
        
        Args:
            data: The data that failed validation
            failure_type: Type of validation failure
            message: Error message
        """
        failure_record = {
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "message": message,
            "data_sample": str(data)[:200]  # Truncate for logging
        }
        self.validation_failures.append(failure_record)
        logger.error(f"Validation failure ({failure_type}): {message}")
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """
        Get data quality metrics
        
        Returns:
            Dictionary containing quality metrics
        """
        if self.data_quality_metrics["total_records"] > 0:
            self.data_quality_metrics["completeness_percentage"] = (
                self.data_quality_metrics["valid_records"] / 
                self.data_quality_metrics["total_records"]
            ) * 100
        
        return self.data_quality_metrics.copy()
    
    def check_quality_threshold(self, threshold: float = 90.0) -> bool:
        """
        Check if data quality meets the specified threshold
        
        Args:
            threshold: Minimum acceptable completeness percentage (default: 90%)
            
        Returns:
            True if quality meets threshold, False otherwise
        """
        metrics = self.get_quality_metrics()
        completeness = metrics["completeness_percentage"]
        
        if completeness < threshold:
            logger.warning(
                f"Data quality below threshold: {completeness:.2f}% < {threshold}%"
            )
            return False
        
        logger.info(f"Data quality acceptable: {completeness:.2f}%")
        return True
    
    def reset_metrics(self):
        """Reset validation metrics"""
        self.validation_failures.clear()
        self.data_quality_metrics = {
            "total_records": 0,
            "valid_records": 0,
            "invalid_records": 0,
            "completeness_percentage": 100.0
        }


# Global instance
validation_engine = ValidationEngine()
