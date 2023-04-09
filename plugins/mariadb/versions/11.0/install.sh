#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

#https://dev.mysql.com/downloads/mysql/5.5.html#downloads
#https://dev.mysql.com/downloads/file/?id=480541

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sysName=`uname`

install_tmp=${rootPath}/tmp/slemp_install.pl
mariadbDir=${serverPath}/source/mariadb

MY_VER=11.0.1

Install_app()
{
	mkdir -p ${mariadbDir}
	echo 'Installing script file...' > $install_tmp

	if id mysql &> /dev/null ;then 
	    echo "mysql uid is `id -u www`"
	    echo "mysql shell is `grep "^www:" /etc/passwd |cut -d':' -f7 `"
	else
	    groupadd mysql
		useradd -g mysql mysql
	fi

	if [ "$sysName" != "Darwin" ];then
		mkdir -p /var/log/mariadb
		touch /var/log/mariadb/mariadb.log
	fi

	# ----- cpu start ------
	if [ -z "${cpuCore}" ]; then
    	cpuCore="1"
	fi

	if [ -f /proc/cpuinfo ];then
		cpuCore=`cat /proc/cpuinfo | grep "processor" | wc -l`
	fi

	MEM_INFO=$(free -m|grep Mem|awk '{printf("%.f",($2)/1024)}')
	if [ "${cpuCore}" != "1" ] && [ "${MEM_INFO}" != "0" ];then
	    if [ "${cpuCore}" -gt "${MEM_INFO}" ];then
	        cpuCore="${MEM_INFO}"
	    fi
	else
	    cpuCore="1"
	fi

	if [ "$cpuCore" -gt "2" ];then
		cpuCore=`echo "$cpuCore" | awk '{printf("%.f",($1)*0.8)}'`
	else
		cpuCore="1"
	fi
	# ----- cpu end ------

	# if [ ! -f ${mariadbDir}/mariadb-${MY_VER}.tar.gz ];then
	# 	wget --no-check-certificate -O ${mariadbDir}/mariadb-${MY_VER}.tar.gz --tries=3 https://mirrors.aliyun.com/mariadb/mariadb-${MY_VER}/source/mariadb-${MY_VER}.tar.gz
	# fi

	# https://downloads.mariadb.org/interstitial/mariadb-10.9.1/source/mariadb-10.9.1.tar.gz
	if [ ! -f ${mariadbDir}/mariadb-${MY_VER}.tar.gz ];then
		wget --no-check-certificate -O ${mariadbDir}/mariadb-${MY_VER}.tar.gz --tries=3 https://archive.mariadb.org/mariadb-${MY_VER}/source/mariadb-${MY_VER}.tar.gz
	fi

	if [ ! -d ${mariadbDir}/mariadb-${MY_VER} ];then
		 cd ${mariadbDir} && tar -zxvf  ${mariadbDir}/mariadb-${MY_VER}.tar.gz
	fi
	

	if [ ! -d $serverPath/mariadb ];then
		cd ${mariadbDir}/mariadb-${MY_VER} && cmake \
		-DCMAKE_INSTALL_PREFIX=$serverPath/mariadb \
		-DMYSQL_DATADIR=$serverPath/mariadb/data/ \
		-DMYSQL_USER=mysql \
		-DMYSQL_UNIX_ADDR=$serverPath/mariadb/mysql.sock \
		-DWITH_MYISAM_STORAGE_ENGINE=1 \
		-DWITH_INNOBASE_STORAGE_ENGINE=1 \
		-DWITH_MEMORY_STORAGE_ENGINE=1 \
		-DENABLED_LOCAL_INFILE=1 \
		-DWITH_PARTITION_STORAGE_ENGINE=1 \
		-DEXTRA_CHARSETS=all \
		-DDEFAULT_CHARSET=utf8mb4 \
		-DDEFAULT_COLLATION=utf8mb4_general_ci \
		-DCMAKE_C_COMPILER=/usr/bin/gcc \
		-DCMAKE_CXX_COMPILER=/usr/bin/g++
		make -j${cpuCore} && make install && make clean

		if [ -d $serverPath/mariadb ];then
			echo '10.11' > $serverPath/mariadb/version.pl
			echo 'The installation is complete' > $install_tmp
		else
			echo 'Installation failed' > $install_tmp
			echo 'install fail'>&2
			exit 1
		fi
	fi

	rm -rf ${mariadbDir}/mariadb-${MY_VER}
	rm -rf ${mariadbDir}/mariadb-${MY_VER}.tar.gz
}

Uninstall_app()
{
	rm -rf $serverPath/mariadb
	echo 'Uninstall complete' > $install_tmp
}

action=$1
if [ "${1}" == 'install' ];then
	Install_app
else
	Uninstall_app
fi
