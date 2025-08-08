#!/bin/bash
set -e

echo "===> Updating SLEMP Panel..."
echo "===> Download panel.zip..."
wget https://github.com/basoro/slemp/archive/refs/heads/sabrina.zip  -O /tmp/panel.zip
unzip /tmp/panel.zip -d /tmp
rm -f /tmp/slemp-sabrina/data/config.json
cp -R /tmp/slemp-sabrina/* /var/www/panel/
rm -rf /tmp/slemp-sabrina

echo "===> Restarting SLEMP Panel..."
supervisorctl restart slemp

supervisorctl start slemp

echo "===> Update complete!"
