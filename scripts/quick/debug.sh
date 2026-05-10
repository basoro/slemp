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
	cd ${rootPath}/plugins/openresty && bash install.sh install 1.21.4.1
fi


# php
# if [ ! -d ${serverPath}/php/71 ];then
# 	cd ${rootPath}/plugins/php && bash install.sh install 71
# fi


PHP_VER_LIST=(53 54 55 56 70 71 72 73 74 80 81 82)
# PHP_VER_LIST=(81)
for PHP_VER in ${PHP_VER_LIST[@]}; do
	echo "php${PHP_VER} -- start"
	if [ ! -d  ${serverPath}/php/${PHP_VER} ];then
		cd ${rootPath}/plugins/php && bash install.sh install ${PHP_VER}
	fi
	echo "php${PHP_VER} -- end"
done


# cd ${rootPath}/plugins/php-yum && bash install.sh install 74


# mysql
if [ ! -d ${serverPath}/mysql ];then
	# cd ${rootPath}/plugins/mysql && bash install.sh install 5.7


	cd ${rootPath}/plugins/mysql && bash install.sh install 5.6
	# cd ${rootPath}/plugins/mysql && bash install.sh install 8.0
fi

endTime=`date +%s`
((outTime=(${endTime}-${startTime})/60))
echo -e "Time consumed:\033[32m $outTime \033[0mMinute!"

} 1> >(tee ${rootPath}/logs/mw-debug.log) 2>&1