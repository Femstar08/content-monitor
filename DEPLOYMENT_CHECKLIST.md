# 🚀 AWS Content Monitor Deployment Checklist

## Pre-Deployment Setup

### 1. Accounts & Services

- [ ] Apify account created (free tier available)
- [ ] VPS/server provisioned (DigitalOcean, AWS EC2, etc.)
- [ ] Vercel account created
- [ ] Domain name configured (optional but recommended)

### 2. Local Development

- [ ] All components running locally
- [ ] Frontend connects to backend successfully
- [ ] Backend mock data working

## 🎯 Deployment Steps

### Step 1: Deploy Apify Actor

```bash
# Install Apify CLI
npm install -g apify-cli

# Login to Apify
apify login

# Deploy actor
chmod +x deploy-apify.sh
./deploy-apify.sh
```

**Verification:**

- [ ] Actor appears in Apify Console
- [ ] Test run completes successfully
- [ ] Note down Actor ID for backend configuration

### Step 2: Deploy Backend to VPS

```bash
# Copy files to VPS
scp -r backend/ user@your-vps:/path/to/deployment/

# SSH into VPS
ssh user@your-vps

# Run deployment script
cd /path/to/deployment/backend
chmod +x deploy-vps.sh
./deploy-vps.sh

# Configure environment
cp .env.example .env
nano .env  # Add your Apify token and other configs
```

**Environment Variables to Set:**

- [ ] `APIFY_TOKEN` - From Apify Console → Settings → Integrations
- [ ] `APIFY_ACTOR_ID` - From deployed actor
- [ ] `CORS_ORIGINS` - Your Vercel frontend URL
- [ ] Other configs as needed

**Verification:**

- [ ] Service running: `sudo systemctl status aws-monitor-api`
- [ ] API accessible: `curl http://your-vps/api/system/health`
- [ ] Nginx configured and running

### Step 3: Deploy Frontend to Vercel

**Option A: Vercel CLI**

```bash
cd frontend
npm install -g vercel
vercel
```

**Option B: GitHub Integration**

1. Push code to GitHub
2. Connect repository to Vercel
3. Configure build settings

**Vercel Configuration:**

- [ ] Framework: Vite
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`

**Environment Variables in Vercel:**

- [ ] `VITE_API_URL` - Your VPS backend URL
- [ ] `VITE_APIFY_ACTOR_ID` - Your actor ID

**Verification:**

- [ ] Frontend loads successfully
- [ ] API calls to backend work
- [ ] All pages and components functional

## 🔧 Post-Deployment Configuration

### SSL/HTTPS Setup

- [ ] SSL certificate installed on VPS (Let's Encrypt recommended)
- [ ] Nginx configured for HTTPS
- [ ] Frontend environment updated with HTTPS URLs

### Monitoring & Logging

- [ ] Backend logs accessible: `journalctl -u aws-monitor-api -f`
- [ ] Apify actor runs monitored in console
- [ ] Frontend error tracking (optional: Sentry)

### Security

- [ ] Firewall configured on VPS
- [ ] API rate limiting implemented (optional)
- [ ] Environment variables secured

## 🧪 Integration Testing

### End-to-End Flow Test

1. [ ] Create monitoring profile in frontend
2. [ ] Trigger actor run from backend
3. [ ] Monitor run status in Apify console
4. [ ] Verify results appear in frontend
5. [ ] Test error handling scenarios

### Performance Testing

- [ ] Frontend loads quickly
- [ ] API responses under 2 seconds
- [ ] Actor runs complete within expected time

## 📋 Architecture Summary

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Backend API    │───▶│  Apify Actor    │
│   (Vercel)      │    │   (Your VPS)     │    │  (Apify Cloud)  │
│                 │    │                  │    │                 │
│ - React/Vite    │    │ - FastAPI        │    │ - Python        │
│ - TypeScript    │    │ - Apify API      │    │ - Web Scraping  │
│ - Tailwind CSS  │    │ - CORS enabled   │    │ - Data Pipeline │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🆘 Troubleshooting

### Common Issues

- **CORS errors**: Check `CORS_ORIGINS` in backend environment
- **Apify API errors**: Verify `APIFY_TOKEN` and `APIFY_ACTOR_ID`
- **Build failures**: Check Node.js version compatibility
- **Service not starting**: Check logs with `journalctl -u aws-monitor-api`

### Useful Commands

```bash
# Backend service management
sudo systemctl restart aws-monitor-api
sudo systemctl status aws-monitor-api
journalctl -u aws-monitor-api -f

# Nginx management
sudo nginx -t
sudo systemctl restart nginx

# Vercel deployment
vercel --prod
vercel logs
```

## ✅ Success Criteria

Your deployment is successful when:

- [ ] Frontend loads at your Vercel URL
- [ ] Backend API responds at your VPS URL
- [ ] You can create and run monitoring profiles
- [ ] Apify actor executes and returns data
- [ ] All three components communicate properly

**Congratulations! Your AWS Content Monitor is now live! 🎉**
