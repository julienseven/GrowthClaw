# $GROWTH Deployment Guide

This guide covers deployment strategies for both frontend and backend components of the $GROWTH autonomous marketing platform.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring & Logging](#monitoring--logging)

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Redis (optional, or use `docker-compose`)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # Add your API keys and settings

# Run development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
# From project root
npm install

# Copy environment template
cp .env.local.example .env.local  # If needed

# Run development server with hot reload
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### Running Both Services

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2 (Frontend):**
```bash
npm run dev
```

---

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Using Docker Compose (Recommended for Local/Staging)

```bash
cd backend

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

This starts:
- **Redis**: `redis://localhost:6379`
- **API**: `http://localhost:8000`

### Building Docker Image Manually

```bash
cd backend

# Build image
docker build -t growth-api:latest .

# Run container
docker run -d \
  --name growth-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e SOLANA_RPC_URL=https://api.mainnet-beta.solana.com \
  -e TARGET_TOKEN_ADDRESS=your-token \
  growth-api:latest

# View logs
docker logs -f growth-api

# Stop container
docker stop growth-api
```

---

## Production Deployment

### Backend Deployment Options

#### Option 1: Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create growth-api

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-key
heroku config:set SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
heroku config:set TARGET_TOKEN_ADDRESS=your-token
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false

# Add Redis add-on
heroku addons:create heroku-redis:premium-0

# Deploy
git push heroku main
```

#### Option 2: AWS Deployment (ECS/Fargate)

```bash
# Create Dockerfile (already included)

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag growth-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/growth-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/growth-api:latest

# Create ECS task definition and service (via AWS Console or CLI)
```

#### Option 3: DigitalOcean App Platform

```bash
# Create app.yaml in backend/
cat > app.yaml << 'EOF'
name: growth-api
services:
- name: api
  github:
    repo: your-github-repo
    branch: main
  source_dir: backend
  build_command: pip install -r requirements.txt
  run_command: uvicorn main:app --host 0.0.0.0 --port 8080
  http_port: 8080
  envs:
  - key: OPENAI_API_KEY
    scope: RUN_AND_BUILD_TIME
    value: ${OPENAI_API_KEY}
  - key: SOLANA_RPC_URL
    value: https://api.mainnet-beta.solana.com
  - key: ENVIRONMENT
    value: production
  - key: DEBUG
    value: "false"
EOF

# Deploy
doctl apps create --spec app.yaml
```

#### Option 4: VPS/Self-Hosted (Recommended for Full Control)

```bash
# SSH into server
ssh root@your-server-ip

# Install dependencies
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip redis-server nginx

# Clone repository
git clone https://github.com/your-repo/growth.git
cd growth/backend

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env with your secrets

# Setup systemd service
sudo tee /etc/systemd/system/growth-api.service > /dev/null << 'EOF'
[Unit]
Description=$GROWTH API
After=network.target

[Service]
Type=notify
User=growth
WorkingDirectory=/root/growth/backend
ExecStart=/root/growth/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Environment="PYTHONUNBUFFERED=1"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable growth-api
sudo systemctl start growth-api

# Configure Nginx reverse proxy
sudo tee /etc/nginx/sites-available/growth-api > /dev/null << 'EOF'
server {
    listen 80;
    server_name api.growth.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/growth-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.growth.example.com
```

### Frontend Deployment Options

#### Option 1: Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_SOLANA_RPC_URL

# Redeploy
vercel --prod
```

#### Option 2: Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy

# Set environment variables in Netlify UI
# Build command: npm run build
# Publish directory: .next
```

#### Option 3: Self-Hosted with Static Export

```bash
# Build static site
npm run build

# Deploy built files to server
scp -r .next root@your-server:/var/www/growth/
scp -r public root@your-server:/var/www/growth/

# Setup Nginx
sudo tee /etc/nginx/sites-available/growth > /dev/null << 'EOF'
server {
    listen 80;
    server_name growth.example.com;
    root /var/www/growth;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://api.growth.example.com;
        proxy_set_header Host $host;
    }
}
EOF
```

---

## Environment Configuration

### Production Environment Variables

#### Backend (.env)
```bash
# Solana
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_NETWORK=mainnet-beta
SOLANA_COMMITMENT_LEVEL=confirmed

# OpenAI (store securely!)
OPENAI_API_KEY=sk-your-production-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# Token Configuration
TARGET_TOKEN_ADDRESS=your-token-mint
TARGET_TOKEN_DECIMALS=6

# Redis (use managed service in production)
REDIS_URL=redis://redis-prod.internal:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_LOG_LEVEL=warning

# Environment
ENVIRONMENT=production
DEBUG=false
```

#### Frontend (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://api.growth.example.com
NEXT_PUBLIC_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

### Secret Management

**Using GitHub Secrets:**
```bash
# Set in repo settings
Settings > Secrets and variables > Actions
- OPENAI_API_KEY
- SOLANA_RPC_URL
- TARGET_TOKEN_ADDRESS
```

**Using Environment Services:**
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- 1Password/Bitwarden

---

## Monitoring & Logging

### Application Health

#### Health Check Endpoint
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "environment": "production",
  "service": "$GROWTH Backend"
}
```

### Logging

#### Backend Logs
```bash
# Docker Compose
docker-compose logs -f api

# Systemd
sudo journalctl -u growth-api -f

# Kubernetes
kubectl logs -f deployment/growth-api
```

#### Structured Logging Setup (Production)

Add to `backend/config/settings.py`:
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': record.created,
            'level': record.levelname,
            'message': record.getMessage(),
            'service': '$GROWTH'
        })
```

### Monitoring Tools

#### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)
```bash
# See backend/docker-compose.yml for additions
docker-compose up elasticsearch kibana
```

#### Option 2: Datadog
```python
# In main.py
from ddtrace import patch_all
patch_all()
```

#### Option 3: Sentry (Error Tracking)
```bash
pip install sentry-sdk
```

```python
# In main.py
import sentry_sdk
sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/your-project-id",
    environment="production"
)
```

### Performance Monitoring

#### FastAPI Middleware
```python
# Add to main.py
from fastapi_prometheus import setup

setup(app)
```

Prometheus metrics available at: `/metrics`

---

## Continuous Deployment Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy $GROWTH

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Heroku
        run: |
          git remote add heroku https://git.heroku.com/growth-api.git
          git push -f heroku main
        env:
          HEROKU_API_KEY: ${{ secrets.HEROKU_API_KEY }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: vercel --prod
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
```

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Run with debug output
PYTHONUNBUFFERED=1 uvicorn main:app --reload
```

### API connection issues
```bash
# Test backend health
curl -v http://localhost:8000/health

# Check environment variables
echo $OPENAI_API_KEY
echo $SOLANA_RPC_URL
```

### Redis connection errors
```bash
# Test Redis connection
redis-cli ping  # Should return PONG

# Check Redis logs
docker-compose logs redis
```

---

## Rollback Procedures

### Heroku
```bash
heroku releases
heroku rollback v5
```

### Docker
```bash
docker pull growth-api:previous-tag
docker stop growth-api
docker run -d --name growth-api growth-api:previous-tag
```

---

**$GROWTH: The Autonomous Marketing Growth Hacker - Ready for Production**
