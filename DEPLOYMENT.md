# 🚀 Civic Bridge - Production Deployment Guide

This guide covers deploying Civic Bridge to production with all the infrastructure components for handling thousands of concurrent users.

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Nginx
- SSL certificate (Let's Encrypt recommended)
- Git

## 🔧 Quick Production Setup

### 1. Run the Automated Setup Script

```bash
# Download and run the production setup script
sudo wget https://raw.githubusercontent.com/YOUR_USERNAME/civic-bridge/main/scripts/setup_production.sh
sudo chmod +x setup_production.sh
sudo ./setup_production.sh
```

The script will:
- Install required packages (Docker, Nginx, PostgreSQL client, etc.)
- Create application user and directories
- Configure firewall and security settings
- Set up automated backups
- Create deployment and monitoring scripts
- Generate secure passwords and configuration

### 2. Clone and Configure the Application

```bash
# Switch to application user
sudo su - civic_bridge

# Clone repository
cd /opt/civic_bridge
git clone https://github.com/YOUR_USERNAME/civic-bridge.git .

# Copy environment configuration
sudo cp .env.example /etc/civic_bridge/.env
sudo chown civic_bridge:civic_bridge /etc/civic_bridge/.env
sudo chmod 600 /etc/civic_bridge/.env

# Edit configuration with your values
sudo nano /etc/civic_bridge/.env
```

### 3. Deploy the Application

```bash
# Run initial deployment
sudo -u civic_bridge /opt/civic_bridge/deploy.sh
```

## 🏗️ Manual Deployment Steps

If you prefer manual setup or need to customize the deployment:

### 1. System Preparation

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install additional tools
apt-get install -y nginx certbot python3-certbot-nginx postgresql-client redis-tools
```

### 2. Create Application Structure

```bash
# Create application user
useradd -r -m -s /bin/bash civic_bridge
usermod -aG docker civic_bridge

# Create directories
mkdir -p /opt/civic_bridge/{logs,data,ssl}
chown -R civic_bridge:civic_bridge /opt/civic_bridge
```

### 3. Configure Environment

```bash
# Create environment file
cat > /etc/civic_bridge/.env << EOF
DATABASE_URL=postgresql://civic_bridge_user:YOUR_DB_PASSWORD@postgres:5432/civic_bridge
POSTGRES_PASSWORD=YOUR_DB_PASSWORD
REDIS_URL=redis://redis:6379/0
SECRET_KEY=YOUR_SECRET_KEY
FLASK_ENV=production
DOMAIN=your-domain.com
EOF

# Secure environment file
chmod 600 /etc/civic_bridge/.env
chown civic_bridge:civic_bridge /etc/civic_bridge/.env
```

### 4. Deploy Application

```bash
# Switch to application user
sudo su - civic_bridge
cd /opt/civic_bridge

# Clone repository
git clone https://github.com/YOUR_USERNAME/civic-bridge.git .

# Start services
docker-compose up -d

# Run database migration
docker-compose run --rm app python database/migrate_csv_to_db.py \
    --host postgres \
    --database civic_bridge \
    --user civic_bridge_user \
    --password YOUR_DB_PASSWORD \
    --create-schema

# Warm cache
docker-compose exec app python -c "
from cache import warm_cache_with_common_queries
warm_cache_with_common_queries()
"
```

### 5. Configure SSL and Nginx

```bash
# Obtain SSL certificate
certbot --nginx -d your-domain.com

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx
```

## 🔍 Health Checks and Monitoring

### Basic Health Check

```bash
# Check application health
curl -f http://localhost/api/health

# Check all services
docker-compose ps

# View logs
docker-compose logs -f app
```

### Comprehensive Health Check

```bash
# Run detailed health check
python /opt/civic_bridge/scripts/health_check.py

# Get JSON output
python /opt/civic_bridge/scripts/health_check.py --json
```

### Monitoring with Prometheus

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Prometheus UI
# http://your-domain.com:9090

# View metrics endpoint
curl http://localhost:5000/metrics
```

## 📊 Performance Tuning

### Database Optimization

```sql
-- Connect to PostgreSQL
\c civic_bridge

-- Analyze tables for query optimization
ANALYZE;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';

-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Cache Optimization

```bash
# Monitor Redis performance
docker-compose exec redis redis-cli info stats

# Check cache hit ratio
curl http://localhost:5000/api/cache/stats

# Warm cache with common queries
curl -X POST http://localhost:5000/api/cache/warm
```

### Application Scaling

```yaml
# Scale application containers
docker-compose up -d --scale app=3

# Update nginx upstream configuration
upstream civic_bridge_backend {
    server app_1:5000;
    server app_2:5000;
    server app_3:5000;
}
```

## 🔒 Security Configuration

### Firewall Setup

```bash
# Configure UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### SSL Configuration

```nginx
# /etc/nginx/sites-available/civic-bridge
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Your location blocks here...
}
```

### Database Security

```sql
-- Create dedicated user with limited privileges
CREATE USER civic_bridge_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE civic_bridge TO civic_bridge_user;
GRANT USAGE ON SCHEMA public TO civic_bridge_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO civic_bridge_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO civic_bridge_user;
```

## 💾 Backup and Recovery

### Automated Backups

```bash
# Backup script runs daily at 2 AM
crontab -l
# 0 2 * * * /opt/civic_bridge/backup.sh

# Manual backup
/opt/civic_bridge/backup.sh

# List backups
ls -la /opt/civic_bridge/backups/
```

### Restore from Backup

```bash
# Stop application
docker-compose down

# Restore database
gunzip -c backup_20240822_020000.sql.gz | docker-compose exec -T postgres psql -U civic_bridge_user civic_bridge

# Start application
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check logs
docker-compose logs app

# Check environment variables
docker-compose exec app env | grep -E "(DATABASE|REDIS|SECRET)"

# Test database connection
docker-compose exec app python -c "
from database.models import db
from api_server import create_app
app = create_app()
with app.app_context():
    db.engine.execute('SELECT 1')
print('Database connection OK')
"
```

**High memory usage:**
```bash
# Check container resource usage
docker stats

# Optimize database connections
# Reduce SQLALCHEMY_ENGINE_OPTIONS pool_size in config

# Monitor PostgreSQL
docker-compose exec postgres psql -U civic_bridge_user civic_bridge -c "
SELECT * FROM pg_stat_activity WHERE state = 'active';
"
```

**Slow performance:**
```bash
# Check slow queries
docker-compose exec postgres psql -U civic_bridge_user civic_bridge -c "
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
"

# Check cache hit ratio
curl http://localhost:5000/api/cache/stats

# Monitor system resources
htop
```

### Log Locations

- Application logs: `/opt/civic_bridge/logs/civic_bridge.log`
- Nginx logs: `/opt/civic_bridge/logs/nginx/`
- Docker logs: `docker-compose logs [service]`
- System logs: `/var/log/syslog`

## 📈 Scaling for High Traffic

### Horizontal Scaling

```bash
# Add more application instances
docker-compose up -d --scale app=5

# Use external load balancer (HAProxy/nginx)
# Configure session stickiness if needed
```

### Database Scaling

```bash
# Set up read replicas
# Configure pgbouncer for connection pooling
# Implement database sharding if needed
```

### Infrastructure Scaling

- Use container orchestration (Kubernetes)
- Implement auto-scaling based on metrics
- Use managed database services (AWS RDS, etc.)
- Implement CDN for static assets

## 🎯 Production Checklist

- [ ] SSL certificate configured and auto-renewal set up
- [ ] Firewall configured and tested
- [ ] Database backups automated and tested
- [ ] Monitoring and alerting configured
- [ ] Log rotation configured
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] Health checks responding
- [ ] Cache warming scheduled
- [ ] Documentation updated
- [ ] Team access configured
- [ ] Incident response plan created

---

## 📞 Support

For deployment issues or questions:
- Create an issue on GitHub
- Check the [troubleshooting guide](TROUBLESHOOTING.md)
- Review application logs and metrics