#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

# cd /Users/midoks/Desktop/slemp/server/panel/plugins/openresty && bash install.sh upgrade 1.29.2
# cd ${rootPath}/plugins/openresty && bash install.sh install 1.21.4
# cd ${rootPath}/plugins/openresty && bash install.sh install 1.29.2
# cd ${rootPath}/plugins/openresty && bash install.sh upgrade 1.29.2

# curl -I -H "Accept-Encoding: br" http://localhost
# curl -I -H "Accept-Encoding: zstd" http://localhost
# curl --http3 -v https://www.xxx.com

# apt install ncat -y
# nc -u -v www.xx.com 443

# cd ${rootPath} && python3 plugins/openresty/index.py run_info

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath

sysName=`uname`
action=$1
type=$2

VERSION=$2
openrestyDir=${serverPath}/source/openresty

if id www &> /dev/null ;then 
    echo "www uid is `id -u www`"
    echo "www shell is `grep "^www:" /etc/passwd |cut -d':' -f7 `"
else
    groupadd www
	useradd -g www -s /bin/bash www
fi

if [ "${action}" == "upgrade" ];then
	sh -x $DIR/versions/$2/install.sh $1
	
	echo "${VERSION}" > $serverPath/openresty/version.pl

	mkdir -p $serverPath/web_conf/php/conf
	echo 'set $PHP_ENV 0;' > $serverPath/web_conf/php/conf/enable-php-00.conf

	#Inisialisasi 
	cd ${rootPath} && python3 ${rootPath}/plugins/openresty/index.py start
	cd ${rootPath} && python3 ${rootPath}/plugins/openresty/index.py initd_install
	exit 0
fi


if [ "${2}" == "" ];then
	echo 'Versi skrip instalasi tidak ditemukan...'
	exit 0
fi 

if [ "${action}" == "uninstall" ];then
	if [ -f /usr/lib/systemd/system/openresty.service ] || [ -f /lib/systemd/system/openresty.service ];then
		systemctl stop openresty
		rm -rf /usr/systemd/system/openresty.service
		rm -rf /lib/systemd/system/openresty.service
		systemctl daemon-reload
	fi

	if [ -f $serverPath/openresty/init.d/openresty ];then
		$serverPath/openresty/init.d/openresty stop
	fi

	rm -rf $serverPath/openresty
fi

sh -x $DIR/versions/$2/install.sh $1

if [ "${action}" == "install" ] && [ -d $serverPath/openresty ];then
	echo "${VERSION}" > $serverPath/openresty/version.pl

	mkdir -p $serverPath/web_conf/php/conf
	echo 'set $PHP_ENV 0;' > $serverPath/web_conf/php/conf/enable-php-00.conf

	#Inisialisasi 
	cd ${rootPath} && python3 ${rootPath}/plugins/openresty/index.py start
	cd ${rootPath} && python3 ${rootPath}/plugins/openresty/index.py initd_install
fi
