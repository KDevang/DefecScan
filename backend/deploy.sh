#!/bin/bash

echo "🚀 Setting up DefecScan Backend on EC2..."

# Update & install dependencies
sudo apt update -y
sudo apt install python3-pip python3-venv nginx -y

# Clone your GitHub repo
cd ~
git clone https://github.com/KDevang/DefecScan.git
cd DefecScan/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend requirements
pip install -r requirements.txt gunicorn

# Start Gunicorn
gunicorn --bind 0.0.0.0:8000 app:app &

# NGINX setup
sudo tee /etc/nginx/sites-available/defecscan <<EOF
server {
    listen 80;
    server_name your_domain_or_public_ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        include proxy_params;
        proxy_redirect off;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/defecscan /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "✅ Backend deployed successfully!"
