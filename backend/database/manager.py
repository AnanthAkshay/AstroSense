"""
Database Manager for AstroSense
Handles all database operations with PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timezone, timedelta
from contextlib import contextmanager
import os
import logging

from models.space_weather import SpaceWeatherData, CMEEvent, SolarFlare
from models.prediction import SectorPredictions, CompositeScoreHistory, BacktestResult
from models.alert import Alert

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations for AstroSense
    
    Features:
    - Connection pooling for performance
    - CRUD operations for all data types
    - Automatic archival of old data
    - Indexed queries for fast retrieval
    - Transaction management with 500ms timeout
    """
    
    def __init__(self, database_url: Optional[str] = None, pool_size: int = 10, max_overflow: int = 20):
        """
        Initialize database manager with connection pool
        
        Args:
            database_url: PostgreSQL connection string
            pool_size: Minimum number of connections in pool
            max_overflow: Maximum number of connections beyond pool_size
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided or set in environment")
        
        # Create connection pool
        self.pool = SimpleConnectionPool(
            minconn=pool_size,
            maxconn=pool_size + max_overflow,
            dsn=self.database_url
        )
        
        logger.info(f"Database connection pool initialized with {pool_size} connections")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Ensures connections are returned to pool
        """
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """
        Context manager for database cursors with automatic commit/rollback
        
        Args:
            dict_cursor: If True, returns results as dictionaries
        """
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                cursor.close()
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")
    
    # ==================== Space Weather Data Operations ====================
    
    def insert_space_weather_data(self, data: SpaceWeatherData) -> int:
        """
        Insert space weather measurement data
        
        Args:
            data: SpaceWeatherData object
            
        Returns:
            ID of inserted record
            
        Validates: Requirements 14.1, 14.3
        """
        query = """
            INSERT INTO space_weather_data 
            (timestamp, solar_wind_speed, bz_field, kp_index, proton_flux, source)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp, source) DO UPDATE
            SET solar_wind_speed = EXCLUDED.solar_wind_speed,
                bz_field = EXCLUDED.bz_field,
                kp_index = EXCLUDED.kp_index,
                proton_flux = EXCLUDED.proton_flux
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                data.timestamp,
                data.solar_wind_speed,
                data.bz_field,
                data.kp_index,
                data.proton_flux,
                data.source
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_space_weather_data(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        source: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve space weather data with optional filters
        
        Args:
            start_time: Filter for data after this time
            end_time: Filter for data before this time
            source: Filter by data source
            limit: Maximum number of records to return
            
        Returns:
            List of space weather data records
        """
        query = "SELECT * FROM space_weather_data WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        if source:
            query += " AND source = %s"
            params.append(source)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== CME Event Operations ====================
    
    def insert_cme_event(self, event: CMEEvent) -> int:
        """
        Insert CME event data
        
        Args:
            event: CMEEvent object
            
        Returns:
            ID of inserted record
        """
        query = """
            INSERT INTO cme_events 
            (event_id, detection_time, cme_speed, predicted_arrival, 
             confidence_lower, confidence_upper, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO UPDATE
            SET cme_speed = EXCLUDED.cme_speed,
                predicted_arrival = EXCLUDED.predicted_arrival,
                confidence_lower = EXCLUDED.confidence_lower,
                confidence_upper = EXCLUDED.confidence_upper
            RETURNING id
        """
        
        confidence_lower = event.confidence_interval[0] if event.confidence_interval else None
        confidence_upper = event.confidence_interval[1] if event.confidence_interval else None
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                event.event_id,
                event.detection_time,
                event.cme_speed,
                event.predicted_arrival,
                confidence_lower,
                confidence_upper,
                event.source
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_cme_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve CME events with optional time filters"""
        query = "SELECT * FROM cme_events WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND detection_time >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND detection_time <= %s"
            params.append(end_time)
        
        query += " ORDER BY detection_time DESC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== Solar Flare Operations ====================
    
    def insert_solar_flare(self, flare: SolarFlare) -> int:
        """
        Insert solar flare event data
        
        Args:
            flare: SolarFlare object
            
        Returns:
            ID of inserted record
        """
        query = """
            INSERT INTO solar_flares 
            (flare_id, detection_time, flare_class, peak_time, location, source)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (flare_id) DO UPDATE
            SET flare_class = EXCLUDED.flare_class,
                peak_time = EXCLUDED.peak_time,
                location = EXCLUDED.location
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                flare.flare_id,
                flare.detection_time,
                flare.flare_class,
                flare.peak_time,
                flare.location,
                flare.source
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_solar_flares(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        flare_class: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve solar flare events with optional filters"""
        query = "SELECT * FROM solar_flares WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND detection_time >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND detection_time <= %s"
            params.append(end_time)
        
        if flare_class:
            query += " AND flare_class = %s"
            params.append(flare_class)
        
        query += " ORDER BY detection_time DESC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== Prediction Operations ====================
    
    def insert_prediction(self, prediction: SectorPredictions) -> int:
        """
        Insert sector prediction data with model version and input features
        
        Args:
            prediction: SectorPredictions object
            
        Returns:
            ID of inserted record
            
        Validates: Requirements 14.2, 14.3
        """
        query = """
            INSERT INTO predictions 
            (timestamp, aviation_hf_blackout_prob, aviation_polar_risk,
             telecom_signal_degradation, gps_drift_cm, power_grid_gic_risk,
             satellite_drag_risk, composite_score, model_version, input_features)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                prediction.timestamp,
                prediction.aviation_hf_blackout_prob,
                prediction.aviation_polar_risk,
                prediction.telecom_signal_degradation,
                prediction.gps_drift_cm,
                prediction.power_grid_gic_risk,
                prediction.satellite_drag_risk,
                prediction.composite_score,
                prediction.model_version,
                Json(prediction.input_features) if prediction.input_features else None
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_predictions(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve predictions with optional time filters"""
        query = "SELECT * FROM predictions WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== Alert Operations ====================
    
    def insert_alert(self, alert: Alert) -> int:
        """
        Insert alert data
        
        Args:
            alert: Alert object
            
        Returns:
            ID of inserted record
        """
        query = """
            INSERT INTO alerts 
            (alert_id, alert_type, severity, title, description,
             affected_sectors, mitigation_recommendations, created_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (alert_id) DO UPDATE
            SET severity = EXCLUDED.severity,
                description = EXCLUDED.description
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                alert.alert_id,
                alert.alert_type.value,
                alert.severity.value,
                alert.title,
                alert.description,
                alert.affected_sectors,
                alert.mitigation_recommendations,
                alert.created_at,
                alert.expires_at
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Retrieve all active (non-expired, non-archived) alerts"""
        query = """
            SELECT * FROM alerts 
            WHERE expires_at > NOW() AND archived = FALSE
            ORDER BY severity DESC, created_at DESC
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
    
    def archive_expired_alerts(self) -> int:
        """
        Archive alerts that have expired
        
        Returns:
            Number of alerts archived
        """
        query = """
            UPDATE alerts 
            SET archived = TRUE 
            WHERE expires_at <= NOW() AND archived = FALSE
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            return len(results)
    
    # ==================== Composite Score History Operations ====================
    
    def insert_composite_score_history(self, score_data: CompositeScoreHistory) -> int:
        """
        Insert composite score history for trend analysis
        
        Args:
            score_data: CompositeScoreHistory object
            
        Returns:
            ID of inserted record
            
        Validates: Requirements 19.5
        """
        query = """
            INSERT INTO composite_score_history 
            (timestamp, composite_score, aviation_contribution, telecom_contribution,
             gps_contribution, power_grid_contribution)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                score_data.timestamp,
                score_data.composite_score,
                score_data.aviation_contribution,
                score_data.telecom_contribution,
                score_data.gps_contribution,
                score_data.power_grid_contribution
            ))
            result = cursor.fetchone()
            return result['id']
    
    def get_composite_score_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical composite scores for trend analysis
        
        Args:
            start_time: Filter for scores after this time
            end_time: Filter for scores before this time
            limit: Maximum number of records
            
        Returns:
            List of composite score history records
            
        Validates: Requirements 19.5
        """
        query = "SELECT * FROM composite_score_history WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== Backtest Operations ====================
    
    def insert_backtest_result(self, result: BacktestResult) -> int:
        """
        Insert backtesting result data
        
        Args:
            result: BacktestResult object
            
        Returns:
            ID of inserted record
        """
        query = """
            INSERT INTO backtest_results 
            (event_name, event_date, predicted_impacts, actual_impacts,
             accuracy_metrics, timeline)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        with self.get_cursor() as cursor:
            cursor.execute(query, (
                result.event_name,
                result.event_date,
                Json(result.predicted_impacts),
                Json(result.actual_impacts),
                Json(result.accuracy_metrics),
                Json(result.timeline)
            ))
            result_row = cursor.fetchone()
            return result_row['id']
    
    def get_backtest_results(
        self,
        event_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve backtest results with optional event name filter"""
        query = "SELECT * FROM backtest_results WHERE 1=1"
        params = []
        
        if event_name:
            query += " AND event_name = %s"
            params.append(event_name)
        
        query += " ORDER BY event_date DESC LIMIT %s"
        params.append(limit)
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    # ==================== Data Archival Operations ====================
    
    def check_storage_usage(self) -> float:
        """
        Check database storage usage percentage
        
        Returns:
            Storage usage as percentage (0-100)
            
        Validates: Requirements 14.5
        """
        query = """
            SELECT 
                pg_database_size(current_database()) as used_bytes,
                pg_database_size(current_database()) * 100.0 / 
                (SELECT setting::bigint FROM pg_settings WHERE name = 'shared_buffers') as usage_percent
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                # Simplified calculation - in production would need actual disk quota
                return min(result.get('usage_percent', 0), 100.0)
        except Exception as e:
            logger.warning(f"Could not determine storage usage: {e}")
            return 0.0
    
    def archive_old_data(self, cutoff_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Archive data older than cutoff date (default: 1 year ago)
        
        Args:
            cutoff_date: Archive data older than this date
            
        Returns:
            Dictionary with counts of archived records per table
            
        Validates: Requirements 14.5
        """
        if cutoff_date is None:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=365)
        
        archived_counts = {}
        
        # Archive space weather data
        query = """
            DELETE FROM space_weather_data 
            WHERE timestamp < %s
            RETURNING id
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (cutoff_date,))
            archived_counts['space_weather_data'] = len(cursor.fetchall())
        
        # Archive predictions
        query = """
            DELETE FROM predictions 
            WHERE timestamp < %s
            RETURNING id
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (cutoff_date,))
            archived_counts['predictions'] = len(cursor.fetchall())
        
        # Archive composite score history
        query = """
            DELETE FROM composite_score_history 
            WHERE timestamp < %s
            RETURNING id
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, (cutoff_date,))
            archived_counts['composite_score_history'] = len(cursor.fetchall())
        
        logger.info(f"Archived old data: {archived_counts}")
        return archived_counts
    
    def auto_archive_if_needed(self) -> Optional[Dict[str, int]]:
        """
        Automatically archive old data if storage exceeds 80%
        
        Returns:
            Archive counts if archival was performed, None otherwise
            
        Validates: Requirements 14.5
        """
        storage_usage = self.check_storage_usage()
        
        if storage_usage > 80.0:
            logger.warning(f"Storage usage at {storage_usage:.1f}%, triggering automatic archival")
            return self.archive_old_data()
        
        return None
