"""
SQLite Database Manager for AstroSense (Development)
Simple SQLite-based database for development without PostgreSQL
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import logging

logger = logging.getLogger(__name__)


class SQLiteManager:
    """
    Simple SQLite database manager for development
    """
    
    def __init__(self, db_path: str = "astrosense.db"):
        """Initialize SQLite database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create all tables
                self.create_auth_tables(cursor)
                self.create_space_weather_tables(cursor)
                
                conn.commit()
                logger.info(f"SQLite database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Context manager for database cursors with automatic commit/rollback"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                cursor.close()
    
    def create_auth_tables(self, cursor):
        """Create authentication tables"""
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # OTPs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otps (
                email TEXT PRIMARY KEY,
                otp_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                attempts INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_otps_expires_at ON otps(expires_at)")
    
    def create_space_weather_tables(self, cursor):
        """Create space weather tables (basic versions)"""
        
        # Space Weather Data Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS space_weather_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                solar_wind_speed REAL,
                bz_field REAL,
                kp_index REAL,
                proton_flux REAL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, source)
            )
        """)
        
        # Predictions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                aviation_hf_blackout_prob REAL,
                aviation_polar_risk REAL,
                telecom_signal_degradation REAL,
                gps_drift_cm REAL,
                power_grid_gic_risk INTEGER,
                satellite_drag_risk INTEGER,
                composite_score REAL,
                model_version TEXT NOT NULL,
                input_features TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alerts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                affected_sectors TEXT,
                mitigation_recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                archived BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_space_weather_timestamp ON space_weather_data(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC)")


# Global SQLite manager instance
sqlite_manager = None

def get_sqlite_manager() -> SQLiteManager:
    """Get SQLite manager instance"""
    global sqlite_manager
    if sqlite_manager is None:
        sqlite_manager = SQLiteManager()
    return sqlite_manager