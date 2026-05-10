#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

# Nama layanan OpenResty
service_name="openresty"

# Periksa apakah OpenResty sedang berjalan
if systemctl is-active --quiet "$service_name"; then
    # Periksa apakah ada proses zombie
    zombie_processes=$(ps -ef | grep -i openresty | grep -v grep | awk '{print $2}' | xargs ps -o state= -p 2>/dev/null | grep -c Z)
    if [ "$zombie_processes" -gt 0 ]; then
        echo "Hentikan proses zombie nginx"
        ps -ef|grep nginx| grep -v grep| awk '{print $2}' | xargs kill -9
        echo "Proses zombie OpenResty terdeteksi, layanan sedang dimulai ulang..."
        systemctl restart "$service_name"
        echo "Layanan telah dimulai ulang"
    else
        echo "OpenResty berjalan normal"
    fi
else
    echo "kill nginx"
    ps -ef|grep nginx| grep -v grep| awk '{print $2}' | xargs kill -9
    echo "OpenResty tidak berjalan, sedang memulai layanan..."
    systemctl start "$service_name"
    echo "Layanan telah dimulai"
fi

NGINX_IDS=`ps -ef|grep nginx | grep -v grep| awk '{print $2}'`
if [ "$NGINX_IDS" == "" ];then
    ps -ef|grep nginx| grep -v grep| awk '{print $2}' | xargs kill -9
    systemctl start "$service_name"
    echo "OpenResty tidak berjalan, sedang memulai layanan..."
fi

