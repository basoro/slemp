#!/bin/bash
set -e

echo "===> Updating SLEMP Panel..."
echo "===> Download panel.zip..."
wget https://github.com/basoro/slemp/archive/refs/heads/sabrina.zip  -O ~/slemp.zip
unzip ~/slemp.zip -d ~/
rm -f ~/slemp-sabrina/data/config.json
cp -aR ~/slemp-sabrina/* /opt/slemp/
rm -rf ~/slemp*

echo "===> Setup Python Virtual Environment..."
python3 -m venv /opt/slemp-venv
/opt/slemp-venv/bin/pip install --upgrade pip

echo "===> Install Python Requirements..."
/opt/slemp-venv/bin/pip install -r /opt/slemp/requirements.txt

echo "===> Restarting SLEMP Panel..."
supervisorctl restart slemp

echo "===> Update complete!"
