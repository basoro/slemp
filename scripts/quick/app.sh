#!/bin/bash
PANEL_DIR=$(cd "$(dirname "$0")/../.."; pwd)

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

if [ ! -d $PANEL_DIR/logs ]; then
	mkdir -p $PANEL_DIR/logs
fi

{

echo "Welcome to SLEMP Panel"

startTime=`date +%s`

if [ ! -d $PANEL_DIR ];then
	echo "slemp not exist!"
	exit 1
fi

# openresty
if [ ! -d $(dirname "$PANEL_DIR")/server/openresty ];then
	cd $PANEL_DIR/plugins/openresty && bash install.sh install 1.21.4.1
else
	echo "openresty alreay exist!"
fi


# php
if [ ! -d $(dirname "$PANEL_DIR")/server/php/71 ];then
	cd $PANEL_DIR/plugins/php && bash install.sh install 71
else
	echo "php71 alreay exist!"
fi


# php
if [ ! -d $(dirname "$PANEL_DIR")/server/php/74 ];then
	cd $PANEL_DIR/plugins/php && bash install.sh install 74
else
	echo "php74 alreay exist!"
fi


# swap
if [ ! -d $(dirname "$PANEL_DIR")/server/swap ];then
	cd $PANEL_DIR/plugins/swap && bash install.sh install 1.1
else
	echo "swap alreay exist!"
fi

# mysql
if [ ! -d $(dirname "$PANEL_DIR")/server/mysql ];then
	cd $PANEL_DIR/plugins/mysql && bash install.sh install 5.6
else
	echo "mysql alreay exist!"
fi

# phpmyadmin
if [ ! -d $(dirname "$PANEL_DIR")/server/phpmyadmin ];then
	cd $PANEL_DIR/plugins/phpmyadmin && bash install.sh install 4.4.15
else
	echo "phpmyadmin alreay exist!"
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee $PANEL_DIR/logs/slemp-app.log) 2>&1
