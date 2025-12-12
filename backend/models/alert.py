"""
Alert data models for AstroSense
Defines alert structures and types
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    """Alert type classification"""
    FLASH = "FLASH"  # Immediate alerts for X-class flares
    FORECAST = "FORECAST"  # CME impact forecasts 24-48 hours ahead


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MODERATE = "MODERATE"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Alert:
    """
    Alert data structure
    
    Attributes:
        alert_id: Unique identifier for the alert
        alert_type: Type of alert (FLASH or FORECAST)
        severity: Severity level
        title: Alert title
        description: Detailed description
        affected_sectors: List of affected infrastructure sectors
        created_at: Alert creation timestamp
        expires_at: Alert expiration timestamp (2 hours after creation)
        mitigation_recommendations: List of recommended actions
        metadata: Additional alert-specific data
    """
    
    def __init__(
        self,
        alert_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        affected_sectors: List[str],
        created_at: datetime,
        expires_at: datetime,
        mitigation_recommendations: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.description = description
        self.affected_sectors = affected_sectors
        self.created_at = created_at
        self.expires_at = expires_at
        self.mitigation_recommendations = mitigation_recommendations
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary representation"""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'affected_sectors': self.affected_sectors,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'mitigation_recommendations': self.mitigation_recommendations,
            'metadata': self.metadata
        }
    
    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if alert has expired"""
        if current_time is None:
            current_time = datetime.utcnow()
        return current_time >= self.expires_at
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create Alert from dictionary"""
        return cls(
            alert_id=data['alert_id'],
            alert_type=AlertType(data['alert_type']),
            severity=AlertSeverity(data['severity']),
            title=data['title'],
            description=data['description'],
            affected_sectors=data['affected_sectors'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            mitigation_recommendations=data['mitigation_recommendations'],
            metadata=data.get('metadata', {})
        )


class FlashAlert(Alert):
    """
    Flash alert for immediate solar flare events
    Generated within 10 seconds of X-class flare detection
    """
    
    def __init__(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        affected_sectors: List[str],
        created_at: datetime,
        expires_at: datetime,
        mitigation_recommendations: List[str],
        flare_class: str,
        detection_time: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            alert_id=alert_id,
            alert_type=AlertType.FLASH,
            severity=severity,
            title=title,
            description=description,
            affected_sectors=affected_sectors,
            created_at=created_at,
            expires_at=expires_at,
            mitigation_recommendations=mitigation_recommendations,
            metadata=metadata or {}
        )
        self.metadata['flare_class'] = flare_class
        self.metadata['detection_time'] = detection_time.isoformat()


class ImpactForecast(Alert):
    """
    Impact forecast for CME effects 24-48 hours ahead
    Includes confidence intervals and predicted impacts
    """
    
    def __init__(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        affected_sectors: List[str],
        created_at: datetime,
        expires_at: datetime,
        mitigation_recommendations: List[str],
        predicted_kp_index: float,
        arrival_time_lower: datetime,
        arrival_time_upper: datetime,
        confidence_percent: float,
        sector_impacts: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            alert_id=alert_id,
            alert_type=AlertType.FORECAST,
            severity=severity,
            title=title,
            description=description,
            affected_sectors=affected_sectors,
            created_at=created_at,
            expires_at=expires_at,
            mitigation_recommendations=mitigation_recommendations,
            metadata=metadata or {}
        )
        self.metadata['predicted_kp_index'] = predicted_kp_index
        self.metadata['arrival_time_lower'] = arrival_time_lower.isoformat()
        self.metadata['arrival_time_upper'] = arrival_time_upper.isoformat()
        self.metadata['confidence_percent'] = confidence_percent
        self.metadata['sector_impacts'] = sector_impacts
