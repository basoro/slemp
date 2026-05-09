#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

DIR=$(cd "$(dirname "$0")"; pwd)
PANEL_DIR=$(dirname "$DIR")
DEV_DIR=$(dirname "$PANEL_DIR")
SERVER_DIR=$DEV_DIR/server

echo "======================================================"
echo "          SLEMP Panel Uninstaller                     "
echo "======================================================"

echo "Are you sure you want to uninstall SLEMP Panel? (y/n)"
read -r answer
if [ "$answer" != "y" ]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo "Do you want to delete all server data (plugins, websites, databases) in $SERVER_DIR and $DEV_DIR/wwwroot? (y/n)"
read -r delete_data

if [ "$delete_data" == "y" ]; then
    echo "Do you want to backup your data (databases and wwwroot) before deletion? (y/n)"
    read -r backup_data

    if [ "$backup_data" == "y" ]; then
        mkdir -p "$DEV_DIR/backup"
        BACKUP_FILE="$DEV_DIR/backup/slemp_uninstall_backup_$(date +%s).tar.gz"
        echo "Backing up data to $BACKUP_FILE..."
        
        BACKUP_PATHS=""
        if [ -d "$DEV_DIR/wwwroot" ]; then
            BACKUP_PATHS="$DEV_DIR/wwwroot"
        fi
        
        if [ -d "$SERVER_DIR/data" ]; then
            BACKUP_PATHS="$BACKUP_PATHS $SERVER_DIR/data"
        fi
        
        if [ -d "$SERVER_DIR/mariadb/data" ]; then
            BACKUP_PATHS="$BACKUP_PATHS $SERVER_DIR/mariadb/data"
        fi

        if [ -d "$SERVER_DIR/mysql/data" ]; then
            BACKUP_PATHS="$BACKUP_PATHS $SERVER_DIR/mysql/data"
        fi
        
        if [ "$BACKUP_PATHS" != "" ]; then
            tar -czf "$BACKUP_FILE" $BACKUP_PATHS
            echo "Backup completed successfully."
        else
            echo "No data directories found to backup."
        fi
    fi
fi

echo "Stopping SLEMP Panel services..."
if [ -f "$PANEL_DIR/scripts/init.d/slemp" ]; then
    bash "$PANEL_DIR/scripts/init.d/slemp" stop
fi

if [ -f /etc/rc.d/init.d/slemp ]; then
    /etc/rc.d/init.d/slemp stop
    rm -f /etc/rc.d/init.d/slemp
    rm -f /usr/bin/slemp
fi

# Kill any lingering panel processes
pids=$(ps aux | grep -E 'gunicorn -c setting.py app:app|task.py' | grep -v grep | awk '{print $2}')
for pid in $pids; do
    kill -9 "$pid" > /dev/null 2>&1
done

if [ "$delete_data" == "y" ]; then
    echo "Stopping and removing plugin services..."
    if [ -f "$SERVER_DIR/openresty/init.d/openresty" ]; then
        bash "$SERVER_DIR/openresty/init.d/openresty" stop
    fi
    if [ -f "$SERVER_DIR/mysql/init.d/mysqld" ]; then
        bash "$SERVER_DIR/mysql/init.d/mysqld" stop
    fi
    if [ -f "$SERVER_DIR/mariadb/init.d/mysqld" ]; then
        bash "$SERVER_DIR/mariadb/init.d/mysqld" stop
    fi
    
    echo "Removing server data directories..."
    rm -rf "$SERVER_DIR"
    rm -rf "$DEV_DIR/wwwroot"
    rm -rf "$DEV_DIR/wwwlogs"
fi

echo "Removing SLEMP Panel directory..."
rm -rf "$PANEL_DIR"

echo "SLEMP Panel has been successfully uninstalled."
