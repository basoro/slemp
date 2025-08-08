#!/bin/bash
set -e

echo "===> Update & Install dependencies..."
apt-get update && \
apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    gcc python3-dev libffi-dev \
    supervisor \
    curl wget zip unzip vim lsb-release ca-certificates && \
apt-get clean && rm -rf /var/lib/apt/lists/*

echo "===> Download panel.zip..."
wget https://github.com/basoro/slemp/archive/refs/heads/sabrina.zip  -O /tmp/panel.zip
unzip /tmp/panel.zip -d /var/www
mv /var/www/slemp-sabrina /var/www/panel
mkdir /var/www/html

echo "===> Setup Python Virtual Environment..."
python3 -m venv /opt/venv
/opt/venv/bin/pip install --upgrade pip

echo "===> Install Python Requirements..."
/opt/venv/bin/pip install -r /var/www/panel/requirements.txt

echo "===> Create supervisord.conf..."
cat <<EOF > /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true 

[program:slemp]
command=/opt/venv/bin/gunicorn app:app --chdir /var/www/panel --bind 0.0.0.0:5000 --worker-class eventlet --workers 1 --timeout 300
autostart=true
autorestart=true
EOF

supervisorctl reread
supervisorctl update
supervisorctl start slemp

echo "===> Setup complete!"
