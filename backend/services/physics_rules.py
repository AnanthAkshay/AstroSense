"""
Physics Rules Engine for Space Weather Impact Prediction
Applies scientific rules based on McPherron relation and CME physics
"""
from typing import Dict, Any, Optional
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PhysicsRulesEngine:
    """
    Applies physics-based rules for space weather impact prediction
    Weight: 40% in fusion model
    """
    
    def __init__(self):
        self.weight = 0.4  # 40% weight in fusion
        self.prediction_log: list = []
    
    def apply_mcpherron_relation(self, bz: float, wind_speed: float) -> float:
        """
        Apply McPherron relation for geomagnetic storm prediction
        
        The McPherron relation states that geomagnetic storms are most likely
        when Bz is strongly negative AND solar wind speed is high.
        
        Storm risk ∝ V * Bz² (when Bz < 0)
        
        Args:
            bz: Bz magnetic field component in nT
            wind_speed: Solar wind speed in km/s
            
        Returns:
            Storm risk score [0, 1]
        """
        # McPherron relation only applies when Bz is negative (southward)
        if bz >= 0:
            logger.debug(f"Bz={bz} nT is positive, low storm risk")
            return 0.1  # Minimal risk when Bz is northward
        
        # Calculate coupling function: V * Bz²
        # Normalize to [0, 1] range
        # Typical severe storm: V=700 km/s, Bz=-20 nT
        # Coupling = 700 * 400 = 280,000
        
        coupling = wind_speed * (bz ** 2)
        
        # Normalize: 0 to 300,000 -> [0, 1]
        max_coupling = 300000
        normalized_coupling = min(coupling / max_coupling, 1.0)
        
        # Apply threshold: significant risk when Bz < -10 nT AND speed > 500 km/s
        if bz < -10 and wind_speed > 500:
            # Amplify risk for strong conditions
            risk = min(normalized_coupling * 1.5, 1.0)
            logger.info(f"McPherron: Strong conditions (Bz={bz} nT, V={wind_speed} km/s) -> risk={risk:.3f}")
        else:
            risk = normalized_coupling
            logger.debug(f"McPherron: Moderate conditions -> risk={risk:.3f}")
        
        return risk
    
    def calculate_cme_impact(self, cme_speed: float) -> float:
        """
        Calculate CME impact severity based on speed
        
        Faster CMEs:
        - Arrive earlier
        - Have greater impact
        - Cause more severe geomagnetic storms
        
        Args:
            cme_speed: CME speed in km/s
            
        Returns:
            Impact severity score [0, 1]
        """
        if cme_speed <= 0:
            return 0.0
        
        # CME speed thresholds:
        # < 500 km/s: Weak
        # 500-1000 km/s: Moderate
        # > 1000 km/s: Strong
        # > 1500 km/s: Extreme
        
        if cme_speed < 500:
            severity = cme_speed / 1000  # 0 to 0.5
        elif cme_speed < 1000:
            severity = 0.5 + (cme_speed - 500) / 1000  # 0.5 to 1.0
        else:
            # Amplify for high-speed CMEs
            severity = min(1.0 + (cme_speed - 1000) / 2000, 1.5)
        
        # Predict earlier arrival for faster CMEs
        if cme_speed > 1000:
            logger.info(f"High-speed CME ({cme_speed} km/s) -> earlier arrival, severity={severity:.3f}")
        
        return min(severity, 1.0)
    
    def check_flare_blackout(self, flare_class: str) -> bool:
        """
        Check if solar flare triggers immediate radio blackout
        
        X-class flares cause immediate HF radio blackouts on sunlit side of Earth
        
        Args:
            flare_class: Flare classification (e.g., "X2.5", "M5.0")
            
        Returns:
            True if immediate blackout expected, False otherwise
        """
        if not flare_class:
            return False
        
        class_letter = flare_class[0].upper()
        
        if class_letter == 'X':
            logger.warning(f"X-class flare detected ({flare_class}) -> IMMEDIATE RADIO BLACKOUT")
            return True
        
        return False
    
    def predict_impacts(self, space_weather_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict sector-specific impacts using physics rules
        
        Args:
            space_weather_data: Dictionary containing space weather measurements
            
        Returns:
            Dictionary of impact predictions for each sector
        """
        # Extract parameters
        bz = space_weather_data.get('bz', 0.0)
        wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        kp_index = space_weather_data.get('kp_index', 3.0)
        flare_class = space_weather_data.get('flare_class', '')
        
        # Apply McPherron relation
        storm_risk = self.apply_mcpherron_relation(bz, wind_speed)
        
        # Calculate CME impact
        cme_impact = self.calculate_cme_impact(cme_speed)
        
        # Check for immediate flare blackout
        immediate_blackout = self.check_flare_blackout(flare_class)
        
        # Combine factors for overall geomagnetic activity
        geomag_activity = (storm_risk * 0.6 + cme_impact * 0.4)
        
        # Predict sector-specific impacts
        predictions = {}
        
        # Aviation: HF blackout probability
        if immediate_blackout:
            predictions['aviation_hf_blackout'] = 95.0  # Immediate blackout
        else:
            # Based on geomagnetic activity and Kp
            predictions['aviation_hf_blackout'] = min(geomag_activity * 80 + kp_index * 5, 100.0)
        
        # Telecom: Signal degradation
        # Depends on ionospheric disturbance (Kp-index and storm risk)
        predictions['telecom_degradation'] = min(storm_risk * 70 + kp_index * 8, 100.0)
        
        # GPS: Positional drift in cm
        # Ionospheric scintillation increases with geomagnetic activity
        predictions['gps_drift_cm'] = geomag_activity * 300 + kp_index * 20
        
        # Power Grid: GIC risk (1-10 scale)
        # Directly related to geomagnetic field variations
        predictions['power_grid_gic'] = max(1, min(int(storm_risk * 8 + kp_index * 0.8) + 1, 10))
        
        # Satellite: Orbital drag risk (1-10 scale)
        # Atmospheric heating during storms increases drag
        predictions['satellite_drag'] = max(1, min(int(geomag_activity * 7 + kp_index * 0.9) + 1, 10))
        
        # Log prediction
        self.prediction_log.append({
            'inputs': {
                'bz': bz,
                'wind_speed': wind_speed,
                'cme_speed': cme_speed,
                'kp_index': kp_index,
                'flare_class': flare_class
            },
            'storm_risk': storm_risk,
            'cme_impact': cme_impact,
            'immediate_blackout': immediate_blackout,
            'predictions': predictions
        })
        
        logger.info(f"Physics predictions: Aviation={predictions['aviation_hf_blackout']:.1f}%, "
                   f"Telecom={predictions['telecom_degradation']:.1f}%, "
                   f"GPS={predictions['gps_drift_cm']:.1f}cm")
        
        return predictions
    
    def get_prediction_confidence(self, space_weather_data: Dict[str, Any]) -> float:
        """
        Estimate confidence in physics-based prediction
        
        Args:
            space_weather_data: Space weather measurements
            
        Returns:
            Confidence score [0, 1]
        """
        # Physics rules are most confident when:
        # 1. Bz is strongly negative (clear McPherron conditions)
        # 2. CME is present
        # 3. X-class flare detected
        
        bz = space_weather_data.get('bz', 0.0)
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        flare_class = space_weather_data.get('flare_class', '')
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence for strong negative Bz
        if bz < -15:
            confidence += 0.2
        elif bz < -10:
            confidence += 0.1
        
        # Increase confidence for CME
        if cme_speed > 800:
            confidence += 0.2
        elif cme_speed > 500:
            confidence += 0.1
        
        # High confidence for X-class flares
        if flare_class and flare_class[0].upper() == 'X':
            confidence += 0.2
        
        return min(confidence, 1.0)


# Global instance
physics_engine = PhysicsRulesEngine()
