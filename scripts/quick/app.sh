#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

if [ ! -d ${rootPath}/logs ]; then
	mkdir -p ${rootPath}/logs
fi

{

echo "welcome to panel panel"

startTime=`date +%s`

if [ ! -d ${rootPath} ];then
	echo "panel not exist!"
	exit 1
fi

# openresty
if [ ! -d ${serverPath}/openresty ];then
	cd ${rootPath}/plugins/openresty && bash install.sh install 1.25.3
else
	echo "openresty alreay exist!"
fi

# redis
if [ ! -d ${serverPath}/redis ];then
	cd ${rootPath}/plugins/redis && bash install.sh install 7.4.3
else
	echo "redis alreay exist!"
fi


# php
if [ ! -d ${serverPath}/php/71 ];then
	cd ${rootPath}/plugins/php && bash install.sh install 71
else
	echo "php71 alreay exist!"
fi


# php
if [ ! -d ${serverPath}/php/74 ];then
	cd ${rootPath}/plugins/php && bash install.sh install 74
else
	echo "php74 alreay exist!"
fi


# swap
if [ ! -d ${serverPath}/swap ];then
	cd ${rootPath}/plugins/swap && bash install.sh install 1.1
else
	echo "swap alreay exist!"
fi

# mysql
if [ ! -d ${serverPath}/mysql ];then
	cd ${rootPath}/plugins/mysql && bash install.sh install 5.7
else
	echo "mysql alreay exist!"
fi

# phpmyadmin
if [ ! -d ${serverPath}/phpmyadmin ];then
	cd ${rootPath}/plugins/phpmyadmin && bash install.sh install 4.4.15
else
	echo "phpmyadmin alreay exist!"
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee ${rootPath}/logs/mw-app.log) 2>&1