#!/bin/bash
# Civic Bridge Production Setup Script
# Sets up the production environment with proper security and configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/civic_bridge"
APP_USER="civic_bridge"
DB_NAME="civic_bridge"
DB_USER="civic_bridge_user"

echo -e "${GREEN}🚀 Civic Bridge Production Setup${NC}"
echo "=================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   exit 1
fi

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local result
    
    read -p "${prompt} [${default}]: " result
    echo "${result:-$default}"
}

echo -e "${YELLOW}📋 Configuration${NC}"
echo "=================="

# Get configuration from user
DOMAIN=$(prompt_with_default "Enter your domain name" "civic-bridge.example.com")
EMAIL=$(prompt_with_default "Enter admin email for SSL certificates" "admin@example.com")
DB_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
REDIS_PASSWORD=$(generate_password)

echo -e "${GREEN}✅ Configuration collected${NC}"

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    fail2ban \
    ufw \
    postgresql-client \
    redis-tools \
    curl \
    htop \
    vim

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Create application user
echo -e "${YELLOW}👤 Creating application user...${NC}"
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
    usermod -aG docker "$APP_USER"
fi

# Create application directory
echo -e "${YELLOW}📁 Creating application directory...${NC}"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/ssl"
mkdir -p "/etc/civic_bridge"

# Set ownership
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Create environment file
echo -e "${YELLOW}⚙️ Creating environment configuration...${NC}"
cat > "/etc/civic_bridge/.env" << EOF
# Civic Bridge Production Environment Configuration
# Generated on $(date)

# Database Configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
POSTGRES_PASSWORD=${DB_PASSWORD}

# Redis Configuration
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Flask Configuration
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production

# Domain Configuration
DOMAIN=${DOMAIN}
ADMIN_EMAIL=${EMAIL}

# Security
RATELIMIT_STORAGE_URL=redis://:${REDIS_PASSWORD}@redis:6379/1

# Monitoring
PROMETHEUS_METRICS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=${APP_DIR}/logs/civic_bridge.log
EOF

# Secure the environment file
chmod 600 "/etc/civic_bridge/.env"
chown "$APP_USER:$APP_USER" "/etc/civic_bridge/.env"

# Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Configure fail2ban
echo -e "${YELLOW}🛡️ Configuring fail2ban...${NC}"
cat > "/etc/fail2ban/jail.local" << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = ${APP_DIR}/logs/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# Create systemd service for the application
echo -e "${YELLOW}🔧 Creating systemd service...${NC}"
cat > "/etc/systemd/system/civic-bridge.service" << EOF
[Unit]
Description=Civic Bridge Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0
User=${APP_USER}
Group=${APP_USER}
EnvironmentFile=/etc/civic_bridge/.env

[Install]
WantedBy=multi-user.target
EOF

# Configure log rotation
echo -e "${YELLOW}📜 Configuring log rotation...${NC}"
cat > "/etc/logrotate.d/civic-bridge" << EOF
${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ${APP_USER} ${APP_USER}
    postrotate
        /usr/bin/docker-compose -f ${APP_DIR}/docker-compose.yml restart app
    endscript
}
EOF

# Create deployment script
echo -e "${YELLOW}📝 Creating deployment script...${NC}"
cat > "${APP_DIR}/deploy.sh" << 'EOF'
#!/bin/bash
# Civic Bridge Deployment Script

set -euo pipefail

APP_DIR="/opt/civic_bridge"
APP_USER="civic_bridge"

cd "$APP_DIR"

echo "🔄 Pulling latest changes..."
git pull origin main

echo "🏗️ Building application..."
docker-compose build --no-cache

echo "🗄️ Running database migrations..."
docker-compose run --rm app python database/migrate_csv_to_db.py \
    --host postgres \
    --database civic_bridge \
    --user civic_bridge_user \
    --create-schema

echo "🚀 Restarting services..."
docker-compose down
docker-compose up -d

echo "🔍 Checking health..."
sleep 30
curl -f http://localhost/api/health || (echo "❌ Health check failed" && exit 1)

echo "✅ Deployment complete!"
EOF

chmod +x "${APP_DIR}/deploy.sh"
chown "$APP_USER:$APP_USER" "${APP_DIR}/deploy.sh"

# Create backup script
echo -e "${YELLOW}💾 Creating backup script...${NC}"
cat > "${APP_DIR}/backup.sh" << EOF
#!/bin/bash
# Civic Bridge Backup Script

set -euo pipefail

BACKUP_DIR="${APP_DIR}/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="\${BACKUP_DIR}/civic_bridge_\${DATE}.sql"

mkdir -p "\$BACKUP_DIR"

echo "🗄️ Creating database backup..."
docker-compose exec -T postgres pg_dump -U ${DB_USER} ${DB_NAME} > "\$DB_BACKUP_FILE"

echo "🗜️ Compressing backup..."
gzip "\$DB_BACKUP_FILE"

echo "🧹 Cleaning old backups (keeping last 7 days)..."
find "\$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "✅ Backup complete: \${DB_BACKUP_FILE}.gz"
EOF

chmod +x "${APP_DIR}/backup.sh"
chown "$APP_USER:$APP_USER" "${APP_DIR}/backup.sh"

# Add backup to crontab
echo -e "${YELLOW}⏰ Setting up automated backups...${NC}"
(crontab -u "$APP_USER" -l 2>/dev/null; echo "0 2 * * * ${APP_DIR}/backup.sh") | crontab -u "$APP_USER" -

# Create monitoring script
echo -e "${YELLOW}📊 Creating monitoring script...${NC}"
cat > "${APP_DIR}/monitor.sh" << EOF
#!/bin/bash
# Civic Bridge Monitoring Script

# Check if all services are running
services=("civic_bridge_postgres" "civic_bridge_redis" "civic_bridge_app" "civic_bridge_nginx")

for service in "\${services[@]}"; do
    if ! docker ps --format "table {{.Names}}" | grep -q "\$service"; then
        echo "❌ Service \$service is not running"
        # Send alert (configure webhook/email as needed)
        exit 1
    fi
done

# Check health endpoint
if ! curl -f http://localhost/api/health >/dev/null 2>&1; then
    echo "❌ Health check failed"
    exit 1
fi

echo "✅ All systems operational"
EOF

chmod +x "${APP_DIR}/monitor.sh"
chown "$APP_USER:$APP_USER" "${APP_DIR}/monitor.sh"

# Display configuration summary
echo -e "${GREEN}🎉 Production setup complete!${NC}"
echo "=================================="
echo "Application directory: $APP_DIR"
echo "Application user: $APP_USER"
echo "Domain: $DOMAIN"
echo "Database password: $DB_PASSWORD"
echo "Secret key: $SECRET_KEY"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Clone your application code to $APP_DIR"
echo "2. Configure SSL with: certbot --nginx -d $DOMAIN"
echo "3. Start the application: systemctl enable civic-bridge && systemctl start civic-bridge"
echo "4. Run initial deployment: sudo -u $APP_USER $APP_DIR/deploy.sh"
echo ""
echo -e "${YELLOW}🔐 Security Notes:${NC}"
echo "- Environment file: /etc/civic_bridge/.env"
echo "- Database password: $DB_PASSWORD"
echo "- Change default passwords before going live"
echo "- Configure monitoring and alerting"
echo ""
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
EOF