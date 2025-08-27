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
unzip /tmp/panel.zip -d /opt
mv /opt/slemp-sabrina /opt/slemp
mkdir /opt/slemp/data/www

echo "===> Setup Python Virtual Environment..."
python3 -m venv /opt/slemp-venv
/opt/slemp-venv/bin/pip install --upgrade pip

echo "===> Install Python Requirements..."
/opt/slemp-venv/bin/pip install -r /opt/slemp/requirements.txt

systemctl start supervisor
systemctl enable supervisor

echo "===> Create supervisord.conf..."
cat <<EOF > /etc/supervisor/conf.d/supervisord.conf
[supervisord]
nodaemon=true 

[program:slemp]
command=/opt/slemp-venv/bin/gunicorn app:app --chdir /opt/slemp --bind 0.0.0.0:7777 --worker-class eventlet --workers 1 --timeout 300
autostart=true
autorestart=true
EOF


supervisorctl reread
supervisorctl update
supervisorctl restart slemp

echo "===> Allowing port via UFW..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 7777/tcp

echo "===> Setup complete!"
