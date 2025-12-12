"""
Monitoring and metrics configuration for production deployment.
Implements health checks, metrics collection, and performance monitoring.
"""

import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    request_count: int
    error_count: int
    avg_response_time: float


class PerformanceMonitor:
    """Production performance monitoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.start_time = time.time()
        
    def record_request(self, response_time: float, is_error: bool = False):
        """Record a request for metrics."""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times for memory efficiency
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        # CPU and memory usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network connections (approximate active connections)
        connections = len(psutil.net_connections(kind='inet'))
        
        # Average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0.0
        )
        
        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            active_connections=connections,
            request_count=self.request_count,
            error_count=self.error_count,
            avg_response_time=avg_response_time
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        metrics = self.get_system_metrics()
        uptime = time.time() - self.start_time
        
        # Determine health status
        is_healthy = (
            metrics.cpu_percent < 80 and
            metrics.memory_percent < 85 and
            metrics.disk_usage_percent < 90
        )
        
        error_rate = (
            self.error_count / self.request_count * 100
            if self.request_count > 0 else 0
        )
        
        return {
            'status': 'healthy' if is_healthy else 'degraded',
            'timestamp': metrics.timestamp,
            'uptime_seconds': uptime,
            'system_metrics': asdict(metrics),
            'error_rate_percent': error_rate,
            'checks': {
                'cpu_ok': metrics.cpu_percent < 80,
                'memory_ok': metrics.memory_percent < 85,
                'disk_ok': metrics.disk_usage_percent < 90,
                'error_rate_ok': error_rate < 5.0
            }
        }
    
    def log_metrics(self):
        """Log current metrics."""
        metrics = self.get_system_metrics()
        self.logger.info(
            f"System metrics - CPU: {metrics.cpu_percent}%, "
            f"Memory: {metrics.memory_percent}%, "
            f"Disk: {metrics.disk_usage_percent}%, "
            f"Requests: {metrics.request_count}, "
            f"Errors: {metrics.error_count}, "
            f"Avg Response: {metrics.avg_response_time:.3f}s"
        )


class DatabaseMonitor:
    """Database connection and performance monitoring."""
    
    def __init__(self, engine):
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get database connection pool status."""
        pool = self.engine.pool
        
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Simple connectivity test
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            response_time = time.time() - start_time
            pool_status = self.get_connection_pool_status()
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time * 1000,
                'pool_status': pool_status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global monitoring instances
performance_monitor = PerformanceMonitor()
database_monitor = None  # Will be initialized with engine


def initialize_database_monitor(engine):
    """Initialize database monitor with engine."""
    global database_monitor
    database_monitor = DatabaseMonitor(engine)


def get_comprehensive_health_check() -> Dict[str, Any]:
    """Get comprehensive health check including all systems."""
    health_data = {
        'application': performance_monitor.get_health_status(),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if database_monitor:
        health_data['database'] = database_monitor.check_database_health()
    
    # Overall status
    app_healthy = health_data['application']['status'] == 'healthy'
    db_healthy = (
        database_monitor is None or 
        health_data.get('database', {}).get('status') == 'healthy'
    )
    
    health_data['overall_status'] = 'healthy' if (app_healthy and db_healthy) else 'degraded'
    
    return health_data