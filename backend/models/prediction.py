"""
Prediction data models for AstroSense
Defines structures for sector-specific predictions and composite scores
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SectorPredictions:
    """
    Sector-specific impact predictions
    
    Attributes:
        timestamp: Prediction timestamp
        aviation_hf_blackout_prob: HF blackout probability (0-100%)
        aviation_polar_risk: Polar route risk score (0-100)
        telecom_signal_degradation: Signal degradation percentage (0-100%)
        gps_drift_cm: GPS positional drift in centimeters
        power_grid_gic_risk: GIC risk level (1-10)
        satellite_drag_risk: Orbital drag risk level (1-10)
        composite_score: Overall system risk score (0-100)
        model_version: ML model version identifier
        input_features: Feature vector used for prediction
    """
    timestamp: datetime
    aviation_hf_blackout_prob: float
    aviation_polar_risk: float
    telecom_signal_degradation: float
    gps_drift_cm: float
    power_grid_gic_risk: int
    satellite_drag_risk: int
    composite_score: float
    model_version: str
    input_features: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'aviation_hf_blackout_prob': self.aviation_hf_blackout_prob,
            'aviation_polar_risk': self.aviation_polar_risk,
            'telecom_signal_degradation': self.telecom_signal_degradation,
            'gps_drift_cm': self.gps_drift_cm,
            'power_grid_gic_risk': self.power_grid_gic_risk,
            'satellite_drag_risk': self.satellite_drag_risk,
            'composite_score': self.composite_score,
            'model_version': self.model_version,
            'input_features': self.input_features
        }


@dataclass
class CompositeScoreHistory:
    """
    Historical composite score with contributing factors
    
    Attributes:
        timestamp: Score calculation timestamp
        composite_score: Overall risk score (0-100)
        aviation_contribution: Aviation sector contribution
        telecom_contribution: Telecom sector contribution
        gps_contribution: GPS sector contribution
        power_grid_contribution: Power grid sector contribution
    """
    timestamp: datetime
    composite_score: float
    aviation_contribution: float
    telecom_contribution: float
    gps_contribution: float
    power_grid_contribution: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'composite_score': self.composite_score,
            'aviation_contribution': self.aviation_contribution,
            'telecom_contribution': self.telecom_contribution,
            'gps_contribution': self.gps_contribution,
            'power_grid_contribution': self.power_grid_contribution
        }


@dataclass
class BacktestResult:
    """
    Backtesting result data
    
    Attributes:
        event_name: Name of historical event
        event_date: Date of the event
        predicted_impacts: Predicted sector impacts
        actual_impacts: Actual observed impacts
        accuracy_metrics: Accuracy comparison metrics
        timeline: Event timeline data
    """
    event_name: str
    event_date: datetime
    predicted_impacts: Dict[str, Any]
    actual_impacts: Dict[str, Any]
    accuracy_metrics: Dict[str, Any]
    timeline: list
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'event_name': self.event_name,
            'event_date': self.event_date.isoformat(),
            'predicted_impacts': self.predicted_impacts,
            'actual_impacts': self.actual_impacts,
            'accuracy_metrics': self.accuracy_metrics,
            'timeline': self.timeline
        }
