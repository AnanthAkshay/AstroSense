"""
Chart Data Service for AstroSense
Formats space weather data for time-series chart visualization
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from models.space_weather import SpaceWeatherData
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ChartDataPoint:
    """
    Single data point for chart visualization
    
    Attributes:
        timestamp: Data point timestamp
        value: Numerical value
        unit: Unit of measurement
        threshold_crossed: Whether this point crosses a critical threshold
        annotation: Optional annotation for threshold crossings
    """
    timestamp: datetime
    value: float
    unit: str
    threshold_crossed: bool = False
    annotation: Optional[str] = None


@dataclass
class ChartSeries:
    """
    Time-series data for chart visualization
    
    Attributes:
        name: Series name (e.g., "Solar Wind Speed", "Bz Magnetic Field")
        unit: Unit of measurement
        data_points: List of chart data points
        time_window_hours: Time window in hours (should be 24)
        resolution_minutes: Data resolution in minutes (should be 5)
        thresholds: Critical threshold values for highlighting
    """
    name: str
    unit: str
    data_points: List[ChartDataPoint]
    time_window_hours: int
    resolution_minutes: int
    thresholds: Dict[str, float]


class ChartDataService:
    """
    Service for formatting space weather data into chart-ready format
    
    Handles solar wind speed and Bz magnetic field time-series data
    according to requirements 10.1, 10.2, 10.3, 10.4
    """
    
    # Critical thresholds for highlighting
    SOLAR_WIND_THRESHOLDS = {
        'moderate': 500.0,  # km/s
        'high': 700.0,      # km/s
        'extreme': 1000.0   # km/s
    }
    
    BZ_THRESHOLDS = {
        'moderate': -5.0,   # nT (negative Bz)
        'high': -10.0,      # nT
        'extreme': -20.0    # nT
    }
    
    def format_solar_wind_chart(self, data: List[SpaceWeatherData]) -> ChartSeries:
        """
        Format solar wind speed data for time-series chart
        
        Args:
            data: List of space weather data points
            
        Returns:
            ChartSeries with solar wind speed data in km/s
            
        Validates: Requirements 10.1, 10.3, 10.4
        """
        logger.info("Formatting solar wind chart data")
        
        # Filter and sort data by timestamp
        wind_data = [d for d in data if d.solar_wind_speed is not None]
        wind_data.sort(key=lambda x: x.timestamp)
        
        # Get last 24 hours of data
        if wind_data:
            latest_time = wind_data[-1].timestamp
            cutoff_time = latest_time - timedelta(hours=24)
            wind_data = [d for d in wind_data if d.timestamp >= cutoff_time]
        
        # Create chart data points
        data_points = []
        for d in wind_data:
            # Check for threshold crossings
            threshold_crossed = False
            annotation = None
            
            if d.solar_wind_speed >= self.SOLAR_WIND_THRESHOLDS['extreme']:
                threshold_crossed = True
                annotation = f"Extreme solar wind: {d.solar_wind_speed:.1f} km/s"
            elif d.solar_wind_speed >= self.SOLAR_WIND_THRESHOLDS['high']:
                threshold_crossed = True
                annotation = f"High solar wind: {d.solar_wind_speed:.1f} km/s"
            elif d.solar_wind_speed >= self.SOLAR_WIND_THRESHOLDS['moderate']:
                threshold_crossed = True
                annotation = f"Moderate solar wind: {d.solar_wind_speed:.1f} km/s"
            
            data_points.append(ChartDataPoint(
                timestamp=d.timestamp,
                value=d.solar_wind_speed,
                unit="km/s",
                threshold_crossed=threshold_crossed,
                annotation=annotation
            ))
        
        return ChartSeries(
            name="Solar Wind Speed",
            unit="km/s",
            data_points=data_points,
            time_window_hours=24,
            resolution_minutes=5,
            thresholds=self.SOLAR_WIND_THRESHOLDS
        )
    
    def format_bz_chart(self, data: List[SpaceWeatherData]) -> ChartSeries:
        """
        Format Bz magnetic field data for time-series chart
        
        Args:
            data: List of space weather data points
            
        Returns:
            ChartSeries with Bz magnetic field data in nT
            
        Validates: Requirements 10.2, 10.3, 10.4
        """
        logger.info("Formatting Bz magnetic field chart data")
        
        # Filter and sort data by timestamp
        bz_data = [d for d in data if d.bz_field is not None]
        bz_data.sort(key=lambda x: x.timestamp)
        
        # Get last 24 hours of data
        if bz_data:
            latest_time = bz_data[-1].timestamp
            cutoff_time = latest_time - timedelta(hours=24)
            bz_data = [d for d in bz_data if d.timestamp >= cutoff_time]
        
        # Create chart data points
        data_points = []
        for d in bz_data:
            # Check for threshold crossings (negative Bz is concerning)
            threshold_crossed = False
            annotation = None
            
            if d.bz_field <= self.BZ_THRESHOLDS['extreme']:
                threshold_crossed = True
                annotation = f"Extreme negative Bz: {d.bz_field:.1f} nT"
            elif d.bz_field <= self.BZ_THRESHOLDS['high']:
                threshold_crossed = True
                annotation = f"High negative Bz: {d.bz_field:.1f} nT"
            elif d.bz_field <= self.BZ_THRESHOLDS['moderate']:
                threshold_crossed = True
                annotation = f"Moderate negative Bz: {d.bz_field:.1f} nT"
            
            data_points.append(ChartDataPoint(
                timestamp=d.timestamp,
                value=d.bz_field,
                unit="nT",
                threshold_crossed=threshold_crossed,
                annotation=annotation
            ))
        
        return ChartSeries(
            name="Bz Magnetic Field",
            unit="nT",
            data_points=data_points,
            time_window_hours=24,
            resolution_minutes=5,
            thresholds=self.BZ_THRESHOLDS
        )
    
    def validate_chart_data(self, chart_series: ChartSeries) -> bool:
        """
        Validate chart data meets requirements
        
        Args:
            chart_series: Chart series to validate
            
        Returns:
            True if valid, False otherwise
            
        Validates: Requirements 10.3
        """
        # Check time window is 24 hours
        if chart_series.time_window_hours != 24:
            logger.warning(f"Invalid time window: {chart_series.time_window_hours} hours (expected 24)")
            return False
        
        # Check resolution is 5 minutes
        if chart_series.resolution_minutes != 5:
            logger.warning(f"Invalid resolution: {chart_series.resolution_minutes} minutes (expected 5)")
            return False
        
        # Check data points have timestamps within 24 hours
        if chart_series.data_points:
            timestamps = [dp.timestamp for dp in chart_series.data_points]
            time_span = max(timestamps) - min(timestamps)
            if time_span > timedelta(hours=24):
                logger.warning(f"Data spans {time_span}, exceeds 24 hours")
                return False
        
        return True
    
    def get_threshold_annotations(self, chart_series: ChartSeries) -> List[Dict[str, Any]]:
        """
        Get threshold crossing annotations for chart display
        
        Args:
            chart_series: Chart series to analyze
            
        Returns:
            List of annotation dictionaries for threshold crossings
            
        Validates: Requirements 10.4
        """
        annotations = []
        
        for point in chart_series.data_points:
            if point.threshold_crossed and point.annotation:
                annotations.append({
                    'timestamp': point.timestamp.isoformat(),
                    'value': point.value,
                    'text': point.annotation,
                    'unit': point.unit
                })
        
        return annotations


# Global instance
chart_data_service = ChartDataService()