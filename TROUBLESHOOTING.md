# AstroSense Troubleshooting Guide

## 🚨 Quick Diagnostics

### System Health Check
```bash
# Run comprehensive health check
./scripts/health_check.sh

# Or manual checks:
curl -f http://localhost/health
docker-compose ps
docker stats --no-stream
```

### Service Status
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# astrosense-backend-prod    Up      0.0.0.0:8000->8000/tcp
# astrosense-frontend-prod   Up      0.0.0.0:3000->3000/tcp
# astrosense-db-prod         Up      5432/tcp
# astrosense-redis-prod      Up      6379/tcp
# astrosense-nginx-prod      Up      0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

---

## 🔍 Common Issues and Solutions

### 1. Application Won't Start

#### Symptoms:
- Services fail to start
- "Connection refused" errors
- Containers exit immediately

#### Diagnosis:
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check system resources
df -h
free -h
```

#### Solutions:

**A. Environment Variables Missing:**
```bash
# Verify all required variables are set
cat .env.production | grep -E "(NASA_DONKI_API_KEY|POSTGRES_PASSWORD|SECRET_KEY)"

# If missing, update .env.production
nano .env.production
```

**B. Port Conflicts:**
```bash
# Check if ports are in use
netstat -tulpn | grep -E "(80|443|8000|3000|5432|6379)"

# Stop conflicting services
sudo systemctl stop apache2  # or nginx, if running outside Docker
sudo systemctl stop postgresql  # if running outside Docker
```

**C. Insufficient Resources:**
```bash
# Check disk space
df -h
# If < 10% free, clean up:
docker system prune -f
rm -rf /var/log/*.log.1

# Check memory
free -h
# If < 1GB free, restart services:
docker-compose -f docker-compose.prod.yml restart
```

### 2. Database Connection Issues

#### Symptoms:
- "Connection to database failed"
- Backend health check fails
- Timeout errors

#### Diagnosis:
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U $POSTGRES_USER

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection from backend
docker-compose -f docker-compose.prod.yml exec backend python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

#### Solutions:

**A. Database Not Ready:**
```bash
# Wait for database to be ready
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 30
docker-compose -f docker-compose.prod.yml up -d backend
```

**B. Connection Pool Exhausted:**
```bash
# Check active connections
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT count(*) as active_connections, 
       setting as max_connections 
FROM pg_stat_activity, pg_settings 
WHERE name = 'max_connections';
"

# If near limit, restart backend to reset pool
docker-compose -f docker-compose.prod.yml restart backend
```

**C. Database Corruption:**
```bash
# Check database integrity
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT datname, pg_size_pretty(pg_database_size(datname)) 
FROM pg_database 
WHERE datname = '$POSTGRES_DB';
"

# If corrupted, restore from backup
docker-compose -f docker-compose.prod.yml stop backend
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/latest_backup.sql
docker-compose -f docker-compose.prod.yml start backend
```

### 3. API Errors and Timeouts

#### Symptoms:
- 500 Internal Server Error
- Request timeouts
- "Service Unavailable" errors

#### Diagnosis:
```bash
# Check API health
curl -v http://localhost:8000/health

# Check backend logs for errors
docker-compose -f docker-compose.prod.yml logs backend | tail -100

# Test specific endpoints
curl -X GET "http://localhost:8000/api/fetch-data" -H "accept: application/json"
```

#### Solutions:

**A. NASA API Key Issues:**
```bash
# Test NASA API directly
curl "https://api.nasa.gov/DONKI/CME?startDate=2024-01-01&endDate=2024-01-02&api_key=$NASA_DONKI_API_KEY"

# If invalid, update key in .env.production
nano .env.production
docker-compose -f docker-compose.prod.yml restart backend
```

**B. Rate Limiting:**
```bash
# Check rate limit headers
curl -I http://localhost/api/fetch-data

# If rate limited, wait or adjust limits in nginx.conf
nano nginx/nginx.conf
# Increase: limit_req zone=api burst=50 nodelay;
docker-compose -f docker-compose.prod.yml restart nginx
```

**C. Memory Issues:**
```bash
# Check backend memory usage
docker stats astrosense-backend-prod --no-stream

# If high memory usage, restart backend
docker-compose -f docker-compose.prod.yml restart backend

# Check for memory leaks
docker-compose -f docker-compose.prod.yml logs backend | grep -i "memory\|oom"
```

### 4. Frontend Loading Issues

#### Symptoms:
- White screen
- JavaScript errors
- Assets not loading

#### Diagnosis:
```bash
# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Test frontend directly
curl -I http://localhost:3000
```

#### Solutions:

**A. Build Issues:**
```bash
# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

**B. Environment Variables:**
```bash
# Check frontend environment
docker-compose -f docker-compose.prod.yml exec frontend env | grep NEXT_PUBLIC

# Update if needed
nano frontend/.env.production
docker-compose -f docker-compose.prod.yml restart frontend
```

**C. Nginx Configuration:**
```bash
# Test nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# If invalid, fix and restart
nano nginx/nginx.conf
docker-compose -f docker-compose.prod.yml restart nginx
```

### 5. SSL/HTTPS Issues

#### Symptoms:
- "Not secure" warning
- SSL certificate errors
- Mixed content warnings

#### Diagnosis:
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout | grep -E "(Not Before|Not After)"

# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check nginx SSL config
docker-compose -f docker-compose.prod.yml exec nginx nginx -T | grep ssl
```

#### Solutions:

**A. Expired Certificate:**
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

**B. Mixed Content:**
```bash
# Update frontend URLs to use HTTPS
nano frontend/.env.production
# Change: NEXT_PUBLIC_API_URL=https://yourdomain.com/api
# Change: NEXT_PUBLIC_WS_URL=wss://yourdomain.com/api/stream

docker-compose -f docker-compose.prod.yml restart frontend
```

### 6. Performance Issues

#### Symptoms:
- Slow response times
- High CPU/memory usage
- Timeouts

#### Diagnosis:
```bash
# Check system resources
htop
iostat -x 1 5

# Check application metrics
curl -s http://localhost:8000/health | jq '.system_metrics'

# Check database performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

#### Solutions:

**A. High CPU Usage:**
```bash
# Identify CPU-intensive processes
docker stats --no-stream

# Scale backend if needed (add more workers)
# Edit docker-compose.prod.yml:
# environment:
#   API_WORKERS: 8  # Increase from 4

docker-compose -f docker-compose.prod.yml up -d backend
```

**B. Memory Issues:**
```bash
# Check memory usage by service
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Restart high-memory services
docker-compose -f docker-compose.prod.yml restart backend

# Increase memory limits if needed
# Edit docker-compose.prod.yml deploy.resources.limits.memory
```

**C. Database Performance:**
```bash
# Analyze and vacuum database
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Check for long-running queries
docker-compose -f docker-compose.prod.yml exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"
```

---

## 🔧 Advanced Diagnostics

### Log Analysis

#### Backend Logs:
```bash
# Error patterns
docker-compose -f docker-compose.prod.yml logs backend | grep -E "(ERROR|CRITICAL|Exception)"

# Performance issues
docker-compose -f docker-compose.prod.yml logs backend | grep -E "(slow|timeout|performance)"

# API requests
docker-compose -f docker-compose.prod.yml logs backend | grep -E "(POST|GET|PUT|DELETE)"
```

#### Database Logs:
```bash
# Connection issues
docker-compose -f docker-compose.prod.yml logs postgres | grep -E "(connection|authentication)"

# Performance issues
docker-compose -f docker-compose.prod.yml logs postgres | grep -E "(slow|lock|deadlock)"
```

#### Nginx Logs:
```bash
# Error responses
docker-compose -f docker-compose.prod.yml logs nginx | grep -E "(4[0-9][0-9]|5[0-9][0-9])"

# High response times
docker-compose -f docker-compose.prod.yml logs nginx | awk '$NF > 2.0 {print}' # > 2 seconds
```

### Network Diagnostics

```bash
# Test internal connectivity
docker-compose -f docker-compose.prod.yml exec backend ping postgres
docker-compose -f docker-compose.prod.yml exec backend ping redis
docker-compose -f docker-compose.prod.yml exec frontend ping backend

# Check port connectivity
docker-compose -f docker-compose.prod.yml exec backend nc -zv postgres 5432
docker-compose -f docker-compose.prod.yml exec backend nc -zv redis 6379
```

### Resource Monitoring

```bash
# Continuous monitoring
watch -n 5 'docker stats --no-stream'

# Disk I/O monitoring
iostat -x 1

# Network monitoring
iftop -i eth0

# Process monitoring
htop
```

---

## 🚑 Emergency Procedures

### Complete System Recovery

1. **Stop all services:**
```bash
docker-compose -f docker-compose.prod.yml down
```

2. **Check system resources:**
```bash
df -h
free -h
docker system df
```

3. **Clean up if needed:**
```bash
docker system prune -f
docker volume prune -f
```

4. **Restore from backup:**
```bash
# Start database only
docker-compose -f docker-compose.prod.yml up -d postgres redis
sleep 30

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < backups/latest_backup.sql

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

### Rollback Deployment

```bash
# Revert to previous version
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>

# Rebuild and deploy
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Emergency Contacts

- **System Administrator:** [contact-info]
- **Database Administrator:** [contact-info]
- **Security Team:** [contact-info]
- **On-call Engineer:** [contact-info]

---

## 📋 Maintenance Checklist

### Daily Checks
- [ ] Service health status
- [ ] Error log review
- [ ] Resource usage check
- [ ] Backup verification

### Weekly Checks
- [ ] Performance metrics review
- [ ] Security log audit
- [ ] Database maintenance
- [ ] SSL certificate validity

### Monthly Checks
- [ ] Full system backup test
- [ ] Security updates
- [ ] Performance optimization
- [ ] Capacity planning review

---

## 📞 Getting Help

### Before Contacting Support

1. **Gather information:**
   - Error messages and logs
   - System resource usage
   - Recent changes made
   - Steps to reproduce the issue

2. **Try basic troubleshooting:**
   - Restart affected services
   - Check environment variables
   - Verify network connectivity
   - Review recent logs

3. **Document the issue:**
   - When did it start?
   - What changed recently?
   - What error messages appear?
   - What troubleshooting steps were tried?

### Support Information

- **Documentation:** This guide and DEPLOYMENT_GUIDE.md
- **Logs Location:** `docker-compose logs` command
- **Configuration Files:** `.env.production`, `docker-compose.prod.yml`
- **Backup Location:** `./backups/` directory