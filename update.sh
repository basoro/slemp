#!/bin/bash
set -e

echo "===> Updating SLEMP Panel..."
echo "===> Download panel.zip..."
wget https://github.com/basoro/slemp/archive/refs/heads/sabrina.zip  -O /tmp/panel.zip
unzip /tmp/panel.zip -d /tmp
rm -f /tmp/slemp-sabrina/data/config.json
cp -aR /tmp/slemp-sabrina/* /var/www/panel/
rm -rf /tmp/slemp-sabrina

echo "===> Setup Python Virtual Environment..."
python3 -m venv /opt/venv
/opt/venv/bin/pip install --upgrade pip

echo "===> Install Python Requirements..."
/opt/venv/bin/pip install -r /var/www/panel/requirements.txt

echo "===> Restarting SLEMP Panel..."
supervisorctl restart slemp

echo "===> Update complete!"
