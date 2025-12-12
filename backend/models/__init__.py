"""Data models for AstroSense"""
from .space_weather import SpaceWeatherData, CMEEvent, SolarFlare
from .prediction import SectorPredictions, CompositeScoreHistory, BacktestResult
from .alert import Alert, AlertType, AlertSeverity, FlashAlert, ImpactForecast
from .auth import User, Session, OTP, LoginRequest, VerifyOTPRequest, AuthResponse

__all__ = [
    'SpaceWeatherData',
    'CMEEvent',
    'SolarFlare',
    'SectorPredictions',
    'CompositeScoreHistory',
    'BacktestResult',
    'Alert',
    'AlertType',
    'AlertSeverity',
    'FlashAlert',
    'ImpactForecast',
    'User',
    'Session',
    'OTP',
    'LoginRequest',
    'VerifyOTPRequest',
    'AuthResponse'
]
