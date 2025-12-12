"""
Sector-Specific Predictors for Space Weather Impact Forecasting
Translates space weather conditions into sector-specific risk assessments
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AviationPredictor:
    """
    Predicts aviation sector impacts from space weather
    - HF blackout probability (0-100%)
    - Polar route risk based on Kp-index and latitude
    """
    
    def __init__(self):
        self.alert_threshold = 70.0  # Alert when risk exceeds 70%
    
    def calculate_hf_blackout_probability(
        self,
        flare_class: str,
        solar_wind_speed: float,
        kp_index: float,
        bz: float
    ) -> float:
        """
        Calculate HF radio blackout probability (0-100%)
        
        Args:
            flare_class: Solar flare classification (X, M, C, B, A)
            solar_wind_speed: Solar wind speed in km/s
            kp_index: Kp geomagnetic index (0-9)
            bz: Bz magnetic field component in nT
            
        Returns:
            HF blackout probability as percentage (0-100)
        """
        # Base probability from flare class
        flare_prob = 0.0
        if flare_class:
            class_letter = flare_class[0].upper()
            if class_letter == 'X':
                flare_prob = 90.0  # X-class: immediate severe blackout
            elif class_letter == 'M':
                flare_prob = 60.0  # M-class: moderate blackout
            elif class_letter == 'C':
                flare_prob = 30.0  # C-class: minor blackout
            elif class_letter == 'B':
                flare_prob = 10.0  # B-class: minimal impact
            else:
                flare_prob = 5.0   # A-class or other: very low
        
        # Additional factors from space weather conditions
        # High Kp-index increases ionospheric disturbance
        kp_factor = min(kp_index * 5.0, 30.0)
        
        # Negative Bz increases geomagnetic activity
        bz_factor = 0.0
        if bz < 0:
            bz_factor = min(abs(bz) * 1.5, 20.0)
        
        # High solar wind speed amplifies effects
        wind_factor = 0.0
        if solar_wind_speed > 500:
            wind_factor = min((solar_wind_speed - 500) / 50, 15.0)
        
        # Combine factors
        total_prob = flare_prob + kp_factor + bz_factor + wind_factor
        
        # Clamp to [0, 100]
        probability = max(0.0, min(total_prob, 100.0))
        
        logger.debug(f"HF blackout: flare={flare_prob}, kp={kp_factor}, "
                    f"bz={bz_factor}, wind={wind_factor} -> {probability:.1f}%")
        
        return probability

    def calculate_polar_route_risk(
        self,
        kp_index: float,
        geomagnetic_latitude: float
    ) -> float:
        """
        Calculate polar route risk based on Kp-index and latitude
        
        Higher latitudes experience greater radiation exposure during storms
        
        Args:
            kp_index: Kp geomagnetic index (0-9)
            geomagnetic_latitude: Geomagnetic latitude in degrees (0-90)
            
        Returns:
            Polar route risk score (0-100)
        """
        # Risk increases with Kp-index
        kp_risk = (kp_index / 9.0) * 60.0
        
        # Risk increases with latitude (polar regions most affected)
        # Significant risk above 60° geomagnetic latitude
        if geomagnetic_latitude >= 60:
            latitude_factor = 1.0 + ((geomagnetic_latitude - 60) / 30.0)
        else:
            latitude_factor = geomagnetic_latitude / 60.0
        
        # Combine factors
        risk = kp_risk * latitude_factor
        
        # Clamp to [0, 100]
        risk = max(0.0, min(risk, 100.0))
        
        logger.debug(f"Polar route risk: Kp={kp_index}, lat={geomagnetic_latitude}° -> {risk:.1f}")
        
        return risk

    def predict(
        self,
        space_weather_data: Dict[str, Any],
        geomagnetic_latitude: float = 70.0
    ) -> Dict[str, Any]:
        """
        Generate aviation sector predictions
        
        Args:
            space_weather_data: Space weather measurements
            geomagnetic_latitude: Geomagnetic latitude for polar route calculation
            
        Returns:
            Dictionary with aviation predictions and alerts
        """
        flare_class = space_weather_data.get('flare_class', '')
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        kp_index = space_weather_data.get('kp_index', 3.0)
        bz = space_weather_data.get('bz', 0.0)
        
        # Calculate predictions
        hf_blackout_prob = self.calculate_hf_blackout_probability(
            flare_class, solar_wind_speed, kp_index, bz
        )
        
        polar_risk = self.calculate_polar_route_risk(kp_index, geomagnetic_latitude)
        
        # Generate alert if threshold exceeded
        alert = None
        if hf_blackout_prob > self.alert_threshold or polar_risk > self.alert_threshold:
            alert = {
                'severity': 'HIGH',
                'message': f'Aviation risk alert: HF blackout {hf_blackout_prob:.1f}%, '
                          f'Polar route risk {polar_risk:.1f}',
                'mitigation': [
                    'Consider rerouting polar flights to lower latitudes',
                    'Prepare backup communication systems',
                    'Monitor space weather updates closely',
                    'Brief flight crews on potential HF radio disruptions'
                ]
            }
            logger.warning(f"Aviation alert generated: {alert['message']}")
        
        # Calculate impact time window (based on CME arrival or immediate for flares)
        impact_window = self._calculate_impact_window(space_weather_data)
        
        result = {
            'hf_blackout_probability': hf_blackout_prob,
            'polar_route_risk': polar_risk,
            'alert': alert,
            'impact_window': impact_window
        }
        
        logger.info(f"Aviation prediction: HF={hf_blackout_prob:.1f}%, Polar={polar_risk:.1f}")
        
        return result

    def _calculate_impact_window(self, space_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate time window for impact forecast
        
        Args:
            space_weather_data: Space weather measurements
            
        Returns:
            Dictionary with start_time and end_time
        """
        flare_class = space_weather_data.get('flare_class', '')
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        
        now = datetime.now(timezone.utc)
        
        # X-class flares cause immediate impact
        if flare_class and flare_class[0].upper() == 'X':
            return {
                'start_time': now.isoformat(),
                'end_time': (now + timedelta(hours=2)).isoformat(),
                'type': 'immediate'
            }
        
        # CME-driven impacts arrive later (only if speed is significant)
        if cme_speed > 100:  # Only calculate for meaningful CME speeds
            # Estimate arrival time based on CME speed
            # Distance to Earth: ~150 million km
            distance_km = 150_000_000
            travel_time_hours = distance_km / cme_speed / 3600
            
            # Cap travel time to reasonable maximum (7 days)
            travel_time_hours = min(travel_time_hours, 168)
            
            arrival_time = now + timedelta(hours=travel_time_hours)
            impact_duration = timedelta(hours=6)  # Typical impact duration
            
            return {
                'start_time': arrival_time.isoformat(),
                'end_time': (arrival_time + impact_duration).isoformat(),
                'type': 'cme_arrival'
            }
        
        # Default: gradual onset over next 6 hours
        return {
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(hours=6)).isoformat(),
            'type': 'gradual'
        }



class TelecomPredictor:
    """
    Predicts telecommunications sector impacts from space weather
    - Signal degradation percentage (0-100%)
    - Moderate threshold: 30%
    - Severe threshold: 60%
    """
    
    def __init__(self):
        self.moderate_threshold = 30.0
        self.severe_threshold = 60.0
    
    def calculate_signal_degradation(
        self,
        kp_index: float,
        bz: float,
        solar_wind_speed: float,
        proton_flux: float = 0.0
    ) -> float:
        """
        Calculate telecommunications signal degradation percentage
        
        Ionospheric disturbances affect radio wave propagation
        
        Args:
            kp_index: Kp geomagnetic index (0-9)
            bz: Bz magnetic field component in nT
            solar_wind_speed: Solar wind speed in km/s
            proton_flux: Proton flux in particles/cm²/s/sr
            
        Returns:
            Signal degradation percentage (0-100)
        """
        # Base degradation from Kp-index
        kp_degradation = (kp_index / 9.0) * 50.0
        
        # Negative Bz increases ionospheric disturbance
        bz_degradation = 0.0
        if bz < 0:
            bz_degradation = min(abs(bz) * 2.0, 30.0)
        
        # High solar wind speed amplifies effects
        wind_degradation = 0.0
        if solar_wind_speed > 500:
            wind_degradation = min((solar_wind_speed - 500) / 40, 20.0)
        
        # Proton flux affects satellite communications
        proton_degradation = min(proton_flux / 100, 15.0)
        
        # Combine factors
        total_degradation = (kp_degradation + bz_degradation + 
                           wind_degradation + proton_degradation)
        
        # Clamp to [0, 100]
        degradation = max(0.0, min(total_degradation, 100.0))
        
        logger.debug(f"Signal degradation: kp={kp_degradation:.1f}, bz={bz_degradation:.1f}, "
                    f"wind={wind_degradation:.1f}, proton={proton_degradation:.1f} "
                    f"-> {degradation:.1f}%")
        
        return degradation

    def predict(self, space_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate telecommunications sector predictions
        
        Args:
            space_weather_data: Space weather measurements
            
        Returns:
            Dictionary with telecom predictions and alerts
        """
        kp_index = space_weather_data.get('kp_index', 3.0)
        bz = space_weather_data.get('bz', 0.0)
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        proton_flux = space_weather_data.get('proton_flux', 0.0)
        
        # Calculate signal degradation
        degradation = self.calculate_signal_degradation(
            kp_index, bz, solar_wind_speed, proton_flux
        )
        
        # Classify severity and generate alerts
        alert = None
        if degradation >= self.severe_threshold:
            alert = {
                'severity': 'CRITICAL',
                'classification': 'severe',
                'message': f'Severe telecommunications degradation: {degradation:.1f}%',
                'mitigation': [
                    'Activate backup communication systems',
                    'Notify customers of potential service disruptions',
                    'Increase monitoring of network performance',
                    'Prepare redundant satellite links'
                ]
            }
            logger.warning(f"CRITICAL telecom alert: {degradation:.1f}% degradation")
        elif degradation >= self.moderate_threshold:
            alert = {
                'severity': 'WARNING',
                'classification': 'moderate',
                'message': f'Moderate telecommunications degradation: {degradation:.1f}%',
                'mitigation': [
                    'Monitor network performance closely',
                    'Prepare backup systems for activation',
                    'Inform technical teams of potential issues'
                ]
            }
            logger.info(f"WARNING telecom alert: {degradation:.1f}% degradation")
        
        # Estimate impact duration
        impact_duration = self._estimate_impact_duration(space_weather_data)
        
        result = {
            'signal_degradation_percent': degradation,
            'classification': 'severe' if degradation >= self.severe_threshold 
                            else 'moderate' if degradation >= self.moderate_threshold 
                            else 'low',
            'alert': alert,
            'impact_duration': impact_duration
        }
        
        logger.info(f"Telecom prediction: {degradation:.1f}% degradation "
                   f"({result['classification']})")
        
        return result

    def _estimate_impact_duration(self, space_weather_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Estimate impact duration with start and end times
        
        Args:
            space_weather_data: Space weather measurements
            
        Returns:
            Dictionary with start_time and end_time
        """
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        kp_index = space_weather_data.get('kp_index', 3.0)
        
        now = datetime.now(timezone.utc)
        
        # CME-driven impacts (only if speed is significant)
        if cme_speed > 100:
            distance_km = 150_000_000
            travel_time_hours = distance_km / cme_speed / 3600
            
            # Cap travel time to reasonable maximum (7 days)
            travel_time_hours = min(travel_time_hours, 168)
            
            start_time = now + timedelta(hours=travel_time_hours)
            
            # Duration depends on storm intensity (Kp-index)
            duration_hours = 4 + (kp_index * 2)  # 4-22 hours
            end_time = start_time + timedelta(hours=duration_hours)
        else:
            # Gradual onset
            start_time = now
            duration_hours = 6 + (kp_index * 1.5)
            end_time = start_time + timedelta(hours=duration_hours)
        
        return {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }



class GPSPredictor:
    """
    Predicts GPS sector impacts from space weather
    - Positional drift in centimeters
    - Moderate warning: 50 cm
    - Critical warning: 200 cm
    """
    
    def __init__(self):
        self.moderate_threshold = 50.0  # cm
        self.critical_threshold = 200.0  # cm
    
    def calculate_positional_drift(
        self,
        kp_index: float,
        bz: float,
        solar_wind_speed: float,
        proton_flux: float = 0.0
    ) -> float:
        """
        Calculate GPS positional drift in centimeters
        
        Ionospheric scintillation causes GPS signal delays
        
        Args:
            kp_index: Kp geomagnetic index (0-9)
            bz: Bz magnetic field component in nT
            solar_wind_speed: Solar wind speed in km/s
            proton_flux: Proton flux in particles/cm²/s/sr
            
        Returns:
            Positional drift in centimeters
        """
        # Base drift from Kp-index (ionospheric disturbance)
        kp_drift = (kp_index / 9.0) * 150.0
        
        # Negative Bz increases ionospheric irregularities
        bz_drift = 0.0
        if bz < 0:
            bz_drift = abs(bz) * 5.0
        
        # High solar wind speed amplifies scintillation
        wind_drift = 0.0
        if solar_wind_speed > 500:
            wind_drift = (solar_wind_speed - 500) / 10
        
        # Proton flux affects ionospheric electron density
        proton_drift = proton_flux / 5
        
        # Combine factors
        total_drift = kp_drift + bz_drift + wind_drift + proton_drift
        
        # Ensure non-negative
        drift = max(0.0, total_drift)
        
        logger.debug(f"GPS drift: kp={kp_drift:.1f}, bz={bz_drift:.1f}, "
                    f"wind={wind_drift:.1f}, proton={proton_drift:.1f} "
                    f"-> {drift:.1f} cm")
        
        return drift

    def determine_geographic_distribution(
        self,
        drift: float,
        kp_index: float
    ) -> Dict[str, Any]:
        """
        Determine geographic distribution of GPS impacts
        
        Higher latitudes experience greater effects
        
        Args:
            drift: Base positional drift in cm
            kp_index: Kp geomagnetic index
            
        Returns:
            Dictionary with regional impact information
        """
        # Define regions with latitude-dependent amplification
        regions = {
            'polar': {
                'name': 'Polar Regions (>60°)',
                'amplification': 1.5,
                'drift': drift * 1.5
            },
            'high_latitude': {
                'name': 'High Latitudes (45-60°)',
                'amplification': 1.2,
                'drift': drift * 1.2
            },
            'mid_latitude': {
                'name': 'Mid Latitudes (30-45°)',
                'amplification': 1.0,
                'drift': drift * 1.0
            },
            'low_latitude': {
                'name': 'Low Latitudes (<30°)',
                'amplification': 0.7,
                'drift': drift * 0.7
            }
        }
        
        # Identify region with greatest drift
        max_region = max(regions.items(), key=lambda x: x[1]['drift'])
        
        return {
            'regions': regions,
            'greatest_impact_region': max_region[0],
            'greatest_impact_drift': max_region[1]['drift']
        }
    
    def predict(self, space_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate GPS sector predictions
        
        Args:
            space_weather_data: Space weather measurements
            
        Returns:
            Dictionary with GPS predictions and alerts
        """
        kp_index = space_weather_data.get('kp_index', 3.0)
        bz = space_weather_data.get('bz', 0.0)
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        proton_flux = space_weather_data.get('proton_flux', 0.0)
        
        # Calculate positional drift
        drift = self.calculate_positional_drift(
            kp_index, bz, solar_wind_speed, proton_flux
        )
        
        # Determine geographic distribution
        geo_distribution = self.determine_geographic_distribution(drift, kp_index)
        
        # Generate alerts based on thresholds
        alert = None
        if drift >= self.critical_threshold:
            alert = {
                'severity': 'CRITICAL',
                'classification': 'critical',
                'message': f'Critical GPS accuracy warning: {drift:.1f} cm drift',
                'mitigation': [
                    'Use differential GPS corrections where available',
                    'Increase position uncertainty margins',
                    'Consider alternative navigation systems',
                    'Warn users of degraded accuracy'
                ]
            }
            logger.warning(f"CRITICAL GPS alert: {drift:.1f} cm drift")
        elif drift >= self.moderate_threshold:
            alert = {
                'severity': 'WARNING',
                'classification': 'moderate',
                'message': f'Moderate GPS accuracy warning: {drift:.1f} cm drift',
                'mitigation': [
                    'Monitor GPS accuracy closely',
                    'Prepare backup navigation systems',
                    'Inform users of potential accuracy degradation'
                ]
            }
            logger.info(f"WARNING GPS alert: {drift:.1f} cm drift")
        
        result = {
            'positional_drift_cm': drift,
            'classification': 'critical' if drift >= self.critical_threshold 
                            else 'moderate' if drift >= self.moderate_threshold 
                            else 'low',
            'geographic_distribution': geo_distribution,
            'alert': alert
        }
        
        logger.info(f"GPS prediction: {drift:.1f} cm drift ({result['classification']})")
        
        return result



class PowerGridPredictor:
    """
    Predicts power grid impacts from space weather
    - GIC (Geomagnetically Induced Currents) risk level (1-10)
    - High-risk alert threshold: 7+
    """
    
    def __init__(self):
        self.high_risk_threshold = 7
    
    def calculate_gic_risk(
        self,
        kp_index: float,
        bz: float,
        solar_wind_speed: float,
        ground_conductivity: float = 0.5,
        grid_topology_factor: float = 1.0
    ) -> int:
        """
        Calculate GIC risk level (1-10 scale)
        
        GICs are driven by rapid changes in geomagnetic field
        
        Args:
            kp_index: Kp geomagnetic index (0-9)
            bz: Bz magnetic field component in nT
            solar_wind_speed: Solar wind speed in km/s
            ground_conductivity: Ground conductivity factor (0-1)
            grid_topology_factor: Grid topology vulnerability (0.5-2.0)
            
        Returns:
            GIC risk level (1-10)
        """
        # Base risk from Kp-index (geomagnetic activity)
        kp_risk = (kp_index / 9.0) * 6.0
        
        # Negative Bz increases geomagnetic field variations
        bz_risk = 0.0
        if bz < 0:
            bz_risk = min(abs(bz) / 10, 3.0)
        
        # High solar wind speed drives stronger currents
        wind_risk = 0.0
        if solar_wind_speed > 500:
            wind_risk = min((solar_wind_speed - 500) / 200, 2.0)
        
        # Combine base factors
        base_risk = kp_risk + bz_risk + wind_risk
        
        # Apply ground conductivity (higher conductivity = higher GIC)
        conductivity_multiplier = 0.5 + (ground_conductivity * 0.5)
        
        # Apply grid topology factor (long transmission lines more vulnerable)
        topology_multiplier = grid_topology_factor
        
        # Calculate final risk
        total_risk = base_risk * conductivity_multiplier * topology_multiplier
        
        # Convert to 1-10 scale
        risk_level = max(1, min(int(round(total_risk)) + 1, 10))
        
        logger.debug(f"GIC risk: kp={kp_risk:.1f}, bz={bz_risk:.1f}, wind={wind_risk:.1f}, "
                    f"conductivity={conductivity_multiplier:.2f}, topology={topology_multiplier:.2f} "
                    f"-> level {risk_level}")
        
        return risk_level

    def predict(
        self,
        space_weather_data: Dict[str, Any],
        ground_conductivity: float = 0.5,
        grid_topology_factor: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate power grid sector predictions
        
        Args:
            space_weather_data: Space weather measurements
            ground_conductivity: Regional ground conductivity (0-1)
            grid_topology_factor: Grid vulnerability factor (0.5-2.0)
            
        Returns:
            Dictionary with power grid predictions and alerts
        """
        kp_index = space_weather_data.get('kp_index', 3.0)
        bz = space_weather_data.get('bz', 0.0)
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        
        # Calculate GIC risk
        gic_risk = self.calculate_gic_risk(
            kp_index, bz, solar_wind_speed,
            ground_conductivity, grid_topology_factor
        )
        
        # Generate alert if high risk
        alert = None
        if gic_risk >= self.high_risk_threshold:
            alert = {
                'severity': 'HIGH',
                'message': f'High GIC risk alert: Level {gic_risk}/10',
                'mitigation': [
                    'Activate transformer protection systems',
                    'Reduce grid loading where possible',
                    'Monitor transformer temperatures closely',
                    'Prepare for potential voltage instabilities',
                    'Have emergency response teams on standby'
                ]
            }
            logger.warning(f"HIGH power grid alert: GIC risk level {gic_risk}")
        
        # Calculate 6-hour advance warning window
        now = datetime.now(timezone.utc)
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        
        if cme_speed > 100:  # Only calculate for meaningful CME speeds
            distance_km = 150_000_000
            travel_time_hours = distance_km / cme_speed / 3600
            travel_time_hours = min(travel_time_hours, 168)  # Cap at 7 days
            warning_time = now + timedelta(hours=max(travel_time_hours - 6, 0))
        else:
            warning_time = now
        
        warning_window = {
            'warning_issued_at': now.isoformat(),
            'impact_expected_at': (now + timedelta(hours=6)).isoformat()
        }
        
        result = {
            'gic_risk_level': gic_risk,
            'classification': 'high' if gic_risk >= self.high_risk_threshold else 'moderate',
            'alert': alert,
            'warning_window': warning_window,
            'ground_conductivity': ground_conductivity,
            'grid_topology_factor': grid_topology_factor
        }
        
        logger.info(f"Power grid prediction: GIC risk level {gic_risk}/10")
        
        return result



class SatellitePredictor:
    """
    Predicts satellite impacts from space weather
    - Orbital drag risk level (1-10)
    - Alert threshold: 6+
    - Multi-satellite prioritization
    """
    
    def __init__(self):
        self.alert_threshold = 6
    
    def calculate_orbital_drag_risk(
        self,
        kp_index: float,
        solar_wind_speed: float,
        proton_flux: float,
        altitude_km: float = 400.0
    ) -> int:
        """
        Calculate satellite orbital drag risk (1-10 scale)
        
        Atmospheric heating during storms increases drag on satellites
        
        Args:
            kp_index: Kp geomagnetic index (0-9)
            solar_wind_speed: Solar wind speed in km/s
            proton_flux: Proton flux in particles/cm²/s/sr
            altitude_km: Satellite altitude in km
            
        Returns:
            Orbital drag risk level (1-10)
        """
        # Base risk from Kp-index (atmospheric heating)
        kp_risk = (kp_index / 9.0) * 5.0
        
        # Solar wind speed increases atmospheric density
        wind_risk = 0.0
        if solar_wind_speed > 500:
            wind_risk = min((solar_wind_speed - 500) / 150, 3.0)
        
        # Proton flux heats upper atmosphere
        proton_risk = min(proton_flux / 200, 2.0)
        
        # Combine base factors
        base_risk = kp_risk + wind_risk + proton_risk
        
        # Altitude factor: lower satellites more affected
        # LEO (Low Earth Orbit): 200-2000 km
        if altitude_km < 600:
            altitude_factor = 1.5  # High drag
        elif altitude_km < 1000:
            altitude_factor = 1.2  # Moderate drag
        else:
            altitude_factor = 0.8  # Lower drag
        
        # Calculate final risk
        total_risk = base_risk * altitude_factor
        
        # Convert to 1-10 scale
        risk_level = max(1, min(int(round(total_risk)) + 1, 10))
        
        logger.debug(f"Orbital drag risk: kp={kp_risk:.1f}, wind={wind_risk:.1f}, "
                    f"proton={proton_risk:.1f}, altitude={altitude_km}km, "
                    f"factor={altitude_factor:.2f} -> level {risk_level}")
        
        return risk_level

    def prioritize_satellites(
        self,
        satellites: List[Dict[str, Any]],
        space_weather_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize satellite alerts based on altitude and mission criticality
        
        Args:
            satellites: List of satellite dictionaries with altitude and criticality
            space_weather_data: Space weather measurements
            
        Returns:
            Sorted list of satellites with risk assessments
        """
        kp_index = space_weather_data.get('kp_index', 3.0)
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        proton_flux = space_weather_data.get('proton_flux', 0.0)
        
        prioritized = []
        
        for sat in satellites:
            altitude = sat.get('altitude_km', 400.0)
            criticality = sat.get('mission_criticality', 1.0)  # 0-2 scale
            
            # Calculate drag risk for this satellite
            drag_risk = self.calculate_orbital_drag_risk(
                kp_index, solar_wind_speed, proton_flux, altitude
            )
            
            # Priority score: risk * criticality
            priority_score = drag_risk * (1 + criticality)
            
            prioritized.append({
                'satellite_id': sat.get('id', 'unknown'),
                'name': sat.get('name', 'Unknown'),
                'altitude_km': altitude,
                'mission_criticality': criticality,
                'drag_risk': drag_risk,
                'priority_score': priority_score
            })
        
        # Sort by priority score (highest first)
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"Prioritized {len(prioritized)} satellites by risk and criticality")
        
        return prioritized
    
    def predict(
        self,
        space_weather_data: Dict[str, Any],
        altitude_km: float = 400.0,
        satellites: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate satellite sector predictions
        
        Args:
            space_weather_data: Space weather measurements
            altitude_km: Default satellite altitude in km
            satellites: Optional list of satellites for multi-satellite analysis
            
        Returns:
            Dictionary with satellite predictions and alerts
        """
        kp_index = space_weather_data.get('kp_index', 3.0)
        solar_wind_speed = space_weather_data.get('solar_wind_speed', 400.0)
        proton_flux = space_weather_data.get('proton_flux', 0.0)
        
        # Calculate orbital drag risk
        drag_risk = self.calculate_orbital_drag_risk(
            kp_index, solar_wind_speed, proton_flux, altitude_km
        )
        
        # Generate alert if threshold exceeded
        alert = None
        if drag_risk >= self.alert_threshold:
            alert = {
                'severity': 'HIGH',
                'message': f'Satellite orbital drag alert: Risk level {drag_risk}/10',
                'mitigation': [
                    'Consider orbit adjustment maneuvers',
                    'Monitor orbital parameters closely',
                    'Prepare for increased fuel consumption',
                    'Update collision avoidance predictions',
                    'Coordinate with space traffic management'
                ]
            }
            logger.warning(f"HIGH satellite alert: Drag risk level {drag_risk}")
        
        # Calculate 24-hour advance notice window
        now = datetime.now(timezone.utc)
        cme_speed = space_weather_data.get('cme_speed', 0.0)
        
        if cme_speed > 100:  # Only calculate for meaningful CME speeds
            distance_km = 150_000_000
            travel_time_hours = distance_km / cme_speed / 3600
            travel_time_hours = min(travel_time_hours, 168)  # Cap at 7 days
            notice_time = now + timedelta(hours=max(travel_time_hours - 24, 0))
        else:
            notice_time = now
        
        advance_notice = {
            'notice_issued_at': now.isoformat(),
            'impact_expected_at': (now + timedelta(hours=24)).isoformat()
        }
        
        # Multi-satellite prioritization
        prioritized_satellites = None
        if satellites:
            prioritized_satellites = self.prioritize_satellites(
                satellites, space_weather_data
            )
        
        result = {
            'orbital_drag_risk': drag_risk,
            'altitude_km': altitude_km,
            'classification': 'high' if drag_risk >= self.alert_threshold else 'moderate',
            'alert': alert,
            'advance_notice': advance_notice,
            'prioritized_satellites': prioritized_satellites
        }
        
        logger.info(f"Satellite prediction: Drag risk level {drag_risk}/10 at {altitude_km}km")
        
        return result


class CompositeScoreCalculator:
    """
    Calculates composite impact score across all sectors
    - Weighted formula: 0.35×Aviation + 0.25×Telecom + 0.20×GPS + 0.20×PowerGrid
    - Scale: 0-100
    - Severity classification: low/moderate/high
    - System-wide alerts for scores > 70
    """
    
    def __init__(self):
        self.high_alert_threshold = 70.0
        self.moderate_threshold = 40.0
        self.weights = {
            'aviation': 0.35,
            'telecom': 0.25,
            'gps': 0.20,
            'power_grid': 0.20
        }
        self.last_score = None
        self.last_timestamp = None
    
    def calculate_composite_score(
        self,
        aviation_risk: float,
        telecom_risk: float,
        gps_risk: float,
        power_grid_risk: float
    ) -> float:
        """
        Calculate composite impact score using weighted formula
        
        Args:
            aviation_risk: Aviation HF blackout probability (0-100)
            telecom_risk: Telecom signal degradation percentage (0-100)
            gps_risk: GPS drift score normalized to 0-100 scale
            power_grid_risk: Power grid GIC risk normalized to 0-100 scale
            
        Returns:
            Composite score (0-100)
        """
        # Apply weighted formula
        composite = (
            self.weights['aviation'] * aviation_risk +
            self.weights['telecom'] * telecom_risk +
            self.weights['gps'] * gps_risk +
            self.weights['power_grid'] * power_grid_risk
        )
        
        # Clamp to [0, 100]
        composite = max(0.0, min(composite, 100.0))
        
        logger.debug(f"Composite score: aviation={aviation_risk:.1f}×{self.weights['aviation']}, "
                    f"telecom={telecom_risk:.1f}×{self.weights['telecom']}, "
                    f"gps={gps_risk:.1f}×{self.weights['gps']}, "
                    f"power_grid={power_grid_risk:.1f}×{self.weights['power_grid']} "
                    f"-> {composite:.1f}")
        
        return composite
    
    def classify_severity(self, score: float) -> str:
        """
        Classify severity based on composite score
        
        Args:
            score: Composite score (0-100)
            
        Returns:
            Severity classification: 'low', 'moderate', or 'high'
        """
        if score >= self.high_alert_threshold:
            return 'high'
        elif score >= self.moderate_threshold:
            return 'moderate'
        else:
            return 'low'
    
    def normalize_gps_drift(self, drift_cm: float) -> float:
        """
        Normalize GPS drift from centimeters to 0-100 scale
        
        Uses 500 cm as maximum expected drift for normalization
        
        Args:
            drift_cm: GPS drift in centimeters
            
        Returns:
            Normalized score (0-100)
        """
        max_drift = 500.0  # Maximum expected drift in cm
        normalized = (drift_cm / max_drift) * 100.0
        return min(normalized, 100.0)
    
    def normalize_gic_risk(self, gic_level: int) -> float:
        """
        Normalize GIC risk from 1-10 scale to 0-100 scale
        
        Args:
            gic_level: GIC risk level (1-10)
            
        Returns:
            Normalized score (0-100)
        """
        # Convert 1-10 to 0-100
        normalized = ((gic_level - 1) / 9.0) * 100.0
        return max(0.0, min(normalized, 100.0))
    
    def log_score_change(
        self,
        new_score: float,
        contributing_factors: Dict[str, float],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Log score changes with timestamps and contributing factors
        
        Args:
            new_score: New composite score
            contributing_factors: Dictionary of sector risks
            timestamp: Timestamp of the score calculation
            
        Returns:
            Dictionary with change information
        """
        change_info = {
            'timestamp': timestamp.isoformat(),
            'new_score': new_score,
            'contributing_factors': contributing_factors
        }
        
        if self.last_score is not None:
            change = new_score - self.last_score
            change_info['previous_score'] = self.last_score
            change_info['change'] = change
            change_info['previous_timestamp'] = self.last_timestamp.isoformat() if self.last_timestamp else None
            
            if abs(change) > 5.0:  # Log significant changes
                logger.info(f"Composite score changed by {change:+.1f}: "
                           f"{self.last_score:.1f} -> {new_score:.1f}")
        else:
            change_info['previous_score'] = None
            change_info['change'] = None
            logger.info(f"Initial composite score: {new_score:.1f}")
        
        # Update last score tracking
        self.last_score = new_score
        self.last_timestamp = timestamp
        
        return change_info
    
    def generate_alert(
        self,
        score: float,
        severity: str,
        contributing_factors: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate system-wide alert for high composite scores
        
        Args:
            score: Composite score
            severity: Severity classification
            contributing_factors: Dictionary of sector risks
            
        Returns:
            Alert dictionary or None if no alert needed
        """
        if score <= self.high_alert_threshold:
            return None
        
        # Identify primary contributors (sectors with highest risk)
        sorted_factors = sorted(
            contributing_factors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_contributors = [
            f"{sector}: {risk:.1f}" 
            for sector, risk in sorted_factors[:2]
        ]
        
        alert = {
            'severity': 'HIGH',
            'classification': 'system_wide',
            'message': f'High composite risk alert: Overall score {score:.1f}/100',
            'composite_score': score,
            'primary_contributors': primary_contributors,
            'mitigation': [
                'Activate emergency response protocols across all sectors',
                'Increase monitoring frequency for all systems',
                'Prepare backup systems and redundancies',
                'Coordinate response across aviation, telecom, GPS, and power sectors',
                'Issue public advisories for affected services'
            ]
        }
        
        logger.warning(f"SYSTEM-WIDE HIGH ALERT: Composite score {score:.1f}/100 "
                      f"(Contributors: {', '.join(primary_contributors)})")
        
        return alert
    
    def calculate(
        self,
        sector_predictions: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate composite score from sector predictions
        
        Args:
            sector_predictions: Dictionary containing predictions from all sectors
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            Dictionary with composite score, severity, alert, and change log
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Extract sector risks
        aviation_risk = sector_predictions.get('aviation', {}).get('hf_blackout_probability', 0.0)
        telecom_risk = sector_predictions.get('telecom', {}).get('signal_degradation_percent', 0.0)
        
        # GPS drift needs normalization
        gps_drift_cm = sector_predictions.get('gps', {}).get('positional_drift_cm', 0.0)
        gps_risk = self.normalize_gps_drift(gps_drift_cm)
        
        # Power grid GIC needs normalization
        gic_level = sector_predictions.get('power_grid', {}).get('gic_risk_level', 1)
        power_grid_risk = self.normalize_gic_risk(gic_level)
        
        # Calculate composite score
        composite_score = self.calculate_composite_score(
            aviation_risk, telecom_risk, gps_risk, power_grid_risk
        )
        
        # Classify severity
        severity = self.classify_severity(composite_score)
        
        # Contributing factors for logging
        contributing_factors = {
            'aviation': aviation_risk,
            'telecom': telecom_risk,
            'gps': gps_risk,
            'power_grid': power_grid_risk
        }
        
        # Log score change
        change_log = self.log_score_change(
            composite_score, contributing_factors, timestamp
        )
        
        # Generate alert if needed
        alert = self.generate_alert(composite_score, severity, contributing_factors)
        
        result = {
            'composite_score': composite_score,
            'severity': severity,
            'contributing_factors': contributing_factors,
            'alert': alert,
            'change_log': change_log,
            'timestamp': timestamp.isoformat()
        }
        
        logger.info(f"Composite score calculated: {composite_score:.1f}/100 ({severity})")
        
        return result


# Global instances
aviation_predictor = AviationPredictor()
telecom_predictor = TelecomPredictor()
gps_predictor = GPSPredictor()
power_grid_predictor = PowerGridPredictor()
satellite_predictor = SatellitePredictor()
composite_score_calculator = CompositeScoreCalculator()
