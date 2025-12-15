#!/bin/bash
# VPS Deployment Script for Backend

echo "🚀 Deploying Backend to VPS..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn

# Create systemd service
sudo tee /etc/systemd/system/aws-monitor-api.service > /dev/null <<EOF
[Unit]
Description=AWS Content Monitor API
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn main:app --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aws-monitor-api
sudo systemctl start aws-monitor-api

# Configure Nginx
sudo tee /etc/nginx/sites-available/aws-monitor-api > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/aws-monitor-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Backend deployed successfully!"
echo "🔗 API available at: http://your-domain.com"
echo "📊 Check status: sudo systemctl status aws-monitor-api"