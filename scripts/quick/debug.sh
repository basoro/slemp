#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

echo "welcome to SLEMP panel"

startTime=`date +%s`

if [ ! -d /home/slemp/server/panel ];then
	echo "SLEMP not exist!"
	exit 1
fi

# openresty
if [ ! -d /home/slemp/server/openresty ];then
	cd /home/slemp/server/panel/plugins/openresty && bash install.sh install 1.21.4.1
fi


# php
# if [ ! -d /home/slemp/server/php/71 ];then
# 	cd /home/slemp/server/panel/plugins/php && bash install.sh install 71
# fi



PHP_VER_LIST=(53 54 55 56 70 71 72 73 74 80 81)
# PHP_VER_LIST=(81)
for PHP_VER in ${PHP_VER_LIST[@]}; do
	echo "php${PHP_VER} -- start"
	if [ ! -d  /home/slemp/server/php/${PHP_VER} ];then
		cd /home/slemp/server/panel/plugins/php && bash install.sh install ${PHP_VER}
	fi
	echo "php${PHP_VER} -- end"
done


# mysql
if [ ! -d /home/slemp/server/mysql ];then
	# cd /home/slemp/server/panel/plugins/mysql && bash install.sh install 5.7


	cd /home/slemp/server/panel/plugins/mysql && bash install.sh install 5.6
	# cd /home/slemp/server/panel/plugins/mysql && bash install.sh install 8.0
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

