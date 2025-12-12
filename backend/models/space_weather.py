"""
Space Weather data models for AstroSense
Defines data structures for space weather measurements and events
"""
from typing import Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SpaceWeatherData:
    """
    Space weather measurement data
    
    Attributes:
        timestamp: Measurement timestamp
        solar_wind_speed: Solar wind speed in km/s
        bz_field: Bz magnetic field component in nT
        kp_index: Geomagnetic activity index (0-9)
        proton_flux: Proton flux in particles/cm²/s/sr
        source: Data source identifier (NASA DONKI or NOAA SWPC)
    """
    timestamp: datetime
    solar_wind_speed: Optional[float]
    bz_field: Optional[float]
    kp_index: Optional[float]
    proton_flux: Optional[float]
    source: str
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'solar_wind_speed': self.solar_wind_speed,
            'bz_field': self.bz_field,
            'kp_index': self.kp_index,
            'proton_flux': self.proton_flux,
            'source': self.source
        }


@dataclass
class CMEEvent:
    """
    Coronal Mass Ejection event data
    
    Attributes:
        event_id: Unique event identifier
        detection_time: CME detection timestamp
        cme_speed: CME speed in km/s
        predicted_arrival: Predicted Earth arrival time
        confidence_interval: Tuple of (lower_bound, upper_bound) for arrival time
        source: Data source identifier
    """
    event_id: str
    detection_time: datetime
    cme_speed: Optional[float]
    predicted_arrival: Optional[datetime]
    confidence_interval: Optional[Tuple[datetime, datetime]]
    source: str
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'event_id': self.event_id,
            'detection_time': self.detection_time.isoformat(),
            'cme_speed': self.cme_speed,
            'predicted_arrival': self.predicted_arrival.isoformat() if self.predicted_arrival else None,
            'confidence_lower': self.confidence_interval[0].isoformat() if self.confidence_interval else None,
            'confidence_upper': self.confidence_interval[1].isoformat() if self.confidence_interval else None,
            'source': self.source
        }


@dataclass
class SolarFlare:
    """
    Solar flare event data
    
    Attributes:
        flare_id: Unique flare identifier
        detection_time: Flare detection timestamp
        flare_class: Flare classification (X, M, C, B, A)
        peak_time: Time of peak intensity
        location: Solar location coordinates
        source: Data source identifier
    """
    flare_id: str
    detection_time: datetime
    flare_class: str
    peak_time: Optional[datetime]
    location: Optional[str]
    source: str
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'flare_id': self.flare_id,
            'detection_time': self.detection_time.isoformat(),
            'flare_class': self.flare_class,
            'peak_time': self.peak_time.isoformat() if self.peak_time else None,
            'location': self.location,
            'source': self.source
        }
