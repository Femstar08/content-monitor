# AWS Content Monitor Deployment Guide

## 1. Deploy Apify Actor

### Prerequisites

- Apify account (free tier available)
- Apify CLI installed: `npm install -g apify-cli`

### Deploy Steps

```bash
# Login to Apify
apify login

# Navigate to project root (where .actor folder is)
cd /path/to/your/project

# Deploy the actor
apify push

# Test the actor
apify call
```

### Files that go to Apify:

- `src/` - All Python scraping logic
- `.actor/` - Apify configuration
- `Dockerfile` - Container setup
- `requirements.txt` - Python dependencies
- `setup.py` - Package configuration

## 2. Deploy Backend to VPS

### Prerequisites

- VPS with Python 3.8+ and pip
- Domain/subdomain for API (optional)
- SSL certificate (recommended)

### VPS Setup

```bash
# On your VPS
git clone your-repo
cd your-repo

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Set environment variables
export APIFY_TOKEN="your-apify-token"
export DATABASE_URL="your-database-url"  # if using database
export CORS_ORIGINS="https://your-frontend-domain.vercel.app"

# Run with production server
pip install gunicorn
gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production Backend Setup (Recommended)

```bash
# Install nginx for reverse proxy
sudo apt install nginx

# Create systemd service
sudo nano /etc/systemd/system/aws-monitor-api.service
```

Service file content:

```ini
[Unit]
Description=AWS Content Monitor API
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/your/project/backend
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/gunicorn main:app --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable aws-monitor-api
sudo systemctl start aws-monitor-api
```

## 3. Deploy Frontend to Vercel

### Prerequisites

- Vercel account
- GitHub repository

### Vercel Setup

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend folder
cd frontend

# Deploy to Vercel
vercel

# Set environment variables in Vercel dashboard:
# VITE_API_URL=https://your-vps-domain.com/api
```

### Alternative: GitHub Integration

1. Push code to GitHub
2. Connect repository to Vercel
3. Set build settings:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

## 4. Environment Configuration

### Backend Environment Variables

```bash
# .env file in backend/
APIFY_TOKEN=your_apify_token_here
APIFY_ACTOR_ID=your_actor_id_here
DATABASE_URL=postgresql://user:pass@localhost/dbname
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
JWT_SECRET=your-jwt-secret
```

### Frontend Environment Variables

```bash
# .env file in frontend/
VITE_API_URL=https://your-backend-domain.com
VITE_APIFY_ACTOR_ID=your_actor_id_here
```

## 5. Integration Testing

### Test the Flow

1. Frontend → Backend API → Apify Actor
2. Verify data flows correctly
3. Test error handling
4. Monitor performance

### Health Checks

- Backend: `GET /api/system/health`
- Apify: Check actor runs in Apify console
- Frontend: Verify UI loads and API calls work
