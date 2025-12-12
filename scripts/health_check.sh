#!/bin/bash

# AstroSense Health Check Script
# Performs comprehensive health checks on all system components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
TIMEOUT=10
HEALTH_ENDPOINT="http://localhost/health"
API_ENDPOINT="http://localhost:8000/health"
FRONTEND_ENDPOINT="http://localhost:3000"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}✗${NC} $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local name=$2
    local timeout=${3:-$TIMEOUT}
    
    if curl -f -s --max-time $timeout "$url" >/dev/null 2>&1; then
        print_status "OK" "$name is responding"
        return 0
    else
        print_status "ERROR" "$name is not responding"
        return 1
    fi
}

# Function to check Docker service
check_docker_service() {
    local service=$1
    local status=$(docker-compose -f $COMPOSE_FILE ps -q $service 2>/dev/null)
    
    if [ -n "$status" ]; then
        local running=$(docker inspect --format='{{.State.Running}}' $status 2>/dev/null)
        if [ "$running" = "true" ]; then
            print_status "OK" "Docker service $service is running"
            return 0
        else
            print_status "ERROR" "Docker service $service is not running"
            return 1
        fi
    else
        print_status "ERROR" "Docker service $service not found"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    print_status "INFO" "Checking system resources..."
    
    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        print_status "OK" "Disk usage: ${disk_usage}%"
    elif [ "$disk_usage" -lt 95 ]; then
        print_status "WARN" "Disk usage: ${disk_usage}% (Warning: >90%)"
    else
        print_status "ERROR" "Disk usage: ${disk_usage}% (Critical: >95%)"
    fi
    
    # Check memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -lt 85 ]; then
        print_status "OK" "Memory usage: ${mem_usage}%"
    elif [ "$mem_usage" -lt 95 ]; then
        print_status "WARN" "Memory usage: ${mem_usage}% (Warning: >85%)"
    else
        print_status "ERROR" "Memory usage: ${mem_usage}% (Critical: >95%)"
    fi
    
    # Check CPU load
    local cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local cpu_usage=$(echo "$cpu_load $cpu_cores" | awk '{printf "%.0f", ($1/$2)*100}')
    
    if [ "$cpu_usage" -lt 80 ]; then
        print_status "OK" "CPU load: ${cpu_load} (${cpu_usage}%)"
    elif [ "$cpu_usage" -lt 90 ]; then
        print_status "WARN" "CPU load: ${cpu_load} (${cpu_usage}%) (Warning: >80%)"
    else
        print_status "ERROR" "CPU load: ${cpu_load} (${cpu_usage}%) (Critical: >90%)"
    fi
}

# Function to check database connectivity
check_database() {
    print_status "INFO" "Checking database connectivity..."
    
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U ${POSTGRES_USER:-astrosense} >/dev/null 2>&1; then
        print_status "OK" "Database is accepting connections"
        
        # Check database size
        local db_size=$(docker-compose -f $COMPOSE_FILE exec -T postgres psql -U ${POSTGRES_USER:-astrosense} -d ${POSTGRES_DB:-astrosense_prod} -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB:-astrosense_prod}'));" 2>/dev/null | xargs)
        if [ -n "$db_size" ]; then
            print_status "OK" "Database size: $db_size"
        fi
        
        return 0
    else
        print_status "ERROR" "Database is not accepting connections"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    print_status "INFO" "Checking Redis connectivity..."
    
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli --no-auth-warning ping >/dev/null 2>&1; then
        print_status "OK" "Redis is responding"
        return 0
    else
        print_status "ERROR" "Redis is not responding"
        return 1
    fi
}

# Function to check SSL certificates
check_ssl_certificates() {
    print_status "INFO" "Checking SSL certificates..."
    
    if [ -f "nginx/ssl/cert.pem" ]; then
        local expiry_date=$(openssl x509 -in nginx/ssl/cert.pem -noout -enddate 2>/dev/null | cut -d= -f2)
        if [ -n "$expiry_date" ]; then
            local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
            local current_epoch=$(date +%s)
            local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [ "$days_until_expiry" -gt 30 ]; then
                print_status "OK" "SSL certificate expires in $days_until_expiry days"
            elif [ "$days_until_expiry" -gt 7 ]; then
                print_status "WARN" "SSL certificate expires in $days_until_expiry days (Warning: <30 days)"
            else
                print_status "ERROR" "SSL certificate expires in $days_until_expiry days (Critical: <7 days)"
            fi
        else
            print_status "ERROR" "Could not read SSL certificate expiry date"
        fi
    else
        print_status "WARN" "SSL certificate not found (nginx/ssl/cert.pem)"
    fi
}

# Function to check log files
check_logs() {
    print_status "INFO" "Checking for recent errors in logs..."
    
    # Check for recent errors in backend logs
    local backend_errors=$(docker-compose -f $COMPOSE_FILE logs --since="1h" backend 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    if [ "$backend_errors" -eq 0 ]; then
        print_status "OK" "No recent backend errors"
    elif [ "$backend_errors" -lt 10 ]; then
        print_status "WARN" "$backend_errors recent backend errors"
    else
        print_status "ERROR" "$backend_errors recent backend errors (>10)"
    fi
    
    # Check for recent errors in nginx logs
    local nginx_errors=$(docker-compose -f $COMPOSE_FILE logs --since="1h" nginx 2>/dev/null | grep -E " 5[0-9][0-9] " | wc -l)
    if [ "$nginx_errors" -eq 0 ]; then
        print_status "OK" "No recent nginx 5xx errors"
    elif [ "$nginx_errors" -lt 5 ]; then
        print_status "WARN" "$nginx_errors recent nginx 5xx errors"
    else
        print_status "ERROR" "$nginx_errors recent nginx 5xx errors (>5)"
    fi
}

# Function to check backup status
check_backups() {
    print_status "INFO" "Checking backup status..."
    
    if [ -d "backups" ]; then
        local latest_backup=$(find backups -name "*.sql*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -n "$latest_backup" ]; then
            local backup_age=$(find "$latest_backup" -mtime +1 2>/dev/null)
            if [ -z "$backup_age" ]; then
                print_status "OK" "Recent backup found: $(basename "$latest_backup")"
            else
                print_status "WARN" "Latest backup is older than 24 hours: $(basename "$latest_backup")"
            fi
        else
            print_status "WARN" "No backups found in backups directory"
        fi
    else
        print_status "WARN" "Backups directory not found"
    fi
}

# Main health check function
main() {
    echo "========================================"
    echo "AstroSense Health Check"
    echo "========================================"
    echo "Timestamp: $(date)"
    echo ""
    
    local overall_status=0
    
    # Check prerequisites
    print_status "INFO" "Checking prerequisites..."
    if ! command_exists docker; then
        print_status "ERROR" "Docker is not installed"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_status "ERROR" "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_status "ERROR" "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    print_status "OK" "Prerequisites check passed"
    echo ""
    
    # Check system resources
    check_system_resources || overall_status=1
    echo ""
    
    # Check Docker services
    print_status "INFO" "Checking Docker services..."
    check_docker_service "postgres" || overall_status=1
    check_docker_service "redis" || overall_status=1
    check_docker_service "backend" || overall_status=1
    check_docker_service "frontend" || overall_status=1
    check_docker_service "nginx" || overall_status=1
    echo ""
    
    # Check service connectivity
    print_status "INFO" "Checking service connectivity..."
    check_database || overall_status=1
    check_redis || overall_status=1
    echo ""
    
    # Check HTTP endpoints
    print_status "INFO" "Checking HTTP endpoints..."
    check_http_endpoint "$HEALTH_ENDPOINT" "Main health endpoint" || overall_status=1
    check_http_endpoint "$API_ENDPOINT" "Backend API" || overall_status=1
    check_http_endpoint "$FRONTEND_ENDPOINT" "Frontend" || overall_status=1
    echo ""
    
    # Check SSL certificates
    check_ssl_certificates
    echo ""
    
    # Check logs for errors
    check_logs
    echo ""
    
    # Check backup status
    check_backups
    echo ""
    
    # Overall status
    echo "========================================"
    if [ $overall_status -eq 0 ]; then
        print_status "OK" "Overall system health: HEALTHY"
        echo "All critical components are functioning normally."
    else
        print_status "ERROR" "Overall system health: DEGRADED"
        echo "One or more critical components have issues."
    fi
    echo "========================================"
    
    exit $overall_status
}

# Run main function
main "$@"