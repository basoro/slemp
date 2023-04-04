#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

if [ ! -d /home/slemp/server/panel/logs ]; then
	mkdir -p /home/slemp/server/panel/logs
fi

{

echo "Welcome to SLEMP Panel"

startTime=`date +%s`

if [ ! -d /home/slemp/server/panel ];then
	echo "slemp not exist!"
	exit 1
fi

# openresty
if [ ! -d /home/slemp/server/openresty ];then
	cd /home/slemp/server/panel/plugins/openresty && bash install.sh install 1.21.4.1
else
	echo "openresty alreay exist!"
fi


# php
if [ ! -d /home/slemp/server/php/71 ];then
	cd /home/slemp/server/panel/plugins/php && bash install.sh install 71
else
	echo "php71 alreay exist!"
fi


# php
if [ ! -d /home/slemp/server/php/74 ];then
	cd /home/slemp/server/panel/plugins/php && bash install.sh install 74
else
	echo "php74 alreay exist!"
fi


# swap
if [ ! -d /home/slemp/server/swap ];then
	cd /home/slemp/server/panel/plugins/swap && bash install.sh install 1.1
else
	echo "swap alreay exist!"
fi

# mysql
if [ ! -d /home/slemp/server/mysql ];then
	cd /home/slemp/server/panel/plugins/mysql && bash install.sh install 5.6
else
	echo "mysql alreay exist!"
fi

# phpmyadmin
if [ ! -d /home/slemp/server/phpmyadmin ];then
	cd /home/slemp/server/panel/plugins/phpmyadmin && bash install.sh install 4.4.15
else
	echo "phpmyadmin alreay exist!"
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee /home/slemp/server/panel/logs/slemp-app.log) 2>&1
