#!/bin/bash
set -e

echo "===> Updating SLEMP Panel..."
echo "===> Download panel.zip..."
wget https://github.com/basoro/slemp/archive/refs/heads/sabrina.zip  -O /tmp/panel.zip
unzip /tmp/panel.zip -d /tmp
cp -R /tmp/slemp-sabrina/* /var/www/panel/
rm -rf /tmp/slemp-sabrina

supervisorctl start slemp

echo "===> Update complete!"
