# -*- coding: utf-8 -*-
#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin:/opt/homebrew/opt/bison/bin
export PATH

#https://dev.mysql.com/downloads/mysql/5.7.html
#https://dev.mysql.com/downloads/file/?id=489855

if [ -z "$rootPath" ]; then
    DIR=$(cd "$(dirname "$0")"; pwd)
    rootPath=$(dirname "$(dirname "$(dirname "$(dirname "$DIR")")")")
    serverPath=$(dirname "$rootPath")
fi
sysName=`uname`

mysqlDir=${serverPath}/source/mysql

VERSION=8.0.37

_os=`uname`
echo "use system: ${_os}"
if [ ${_os} == "Darwin" ]; then
	OSNAME='macos'
elif grep -Eq "openSUSE" /etc/*-release; then
	OSNAME='opensuse'
	zypper refresh
elif grep -Eq "FreeBSD" /etc/*-release; then
	OSNAME='freebsd'
	pkg install -y wget unzip
elif grep -Eqi "Arch" /etc/issue || grep -Eq "Arch" /etc/*-release; then
	OSNAME='arch'
	echo y | pacman -Sy unzip
elif grep -Eqi "CentOS" /etc/issue || grep -Eq "CentOS" /etc/*-release; then
	OSNAME='centos'
	yum install -y wget zip unzip
elif grep -Eqi "Fedora" /etc/issue || grep -Eq "Fedora" /etc/*-release; then
	OSNAME='fedora'
	yum install -y wget zip unzip
elif grep -Eqi "Rocky" /etc/issue || grep -Eq "Rocky" /etc/*-release; then
	OSNAME='rocky'
	yum install -y wget zip unzip
elif grep -Eqi "AlmaLinux" /etc/issue || grep -Eq "AlmaLinux" /etc/*-release; then
	OSNAME='alma'
	yum install -y wget zip unzip
elif grep -Eqi "Debian" /etc/issue || grep -Eq "Debian" /etc/*-release; then
	OSNAME='debian'
	apt update -y
	apt install -y devscripts
	apt install -y wget zip unzip
elif grep -Eqi "Ubuntu" /etc/issue || grep -Eq "Ubuntu" /etc/*-release; then
	OSNAME='ubuntu'
	apt install -y wget zip unzip
else
	OSNAME='unknow'
fi

if [ "$OSNAME" != "macos" ];then
	VERSION_ID=`cat /etc/*-release | grep VERSION_ID | awk -F = '{print $2}' | awk -F "\"" '{print $2}'`
fi

Install_mysql()
{
	mkdir -p ${mysqlDir}
	echo 'Sedang menginstal file skrip...'

	# ----- cpu start ------
	if [ -z "${cpuCore}" ]; then
    	cpuCore="1"
	fi

	if [ "$sysName" == "Darwin" ];then
		cpuCore=`sysctl -n hw.ncpu`
	elif [ -f /proc/cpuinfo ];then
		cpuCore=`cat /proc/cpuinfo | grep "processor" | wc -l`
	fi

	if [ "$sysName" == "Darwin" ];then
		MEM_INFO=`sysctl -n hw.memsize | awk '{printf("%.f",$1/1024/1024/1024)}'`
	else
		MEM_INFO=$(free -m|grep Mem|awk '{printf("%.f",($2)/1024)}')
	fi

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

	cd ${rootPath}/plugins/mysql/lib && /bin/bash rpcgen.sh

	INSTALL_CMD=cmake
	# check cmake version
	CMAKE_VERSION=`cmake -version | grep version | awk '{print $3}' | awk -F '.' '{print $1}'`
	if [ "$CMAKE_VERSION" -eq "2" ];then
		mkdir -p /var/log/mariadb
		touch /var/log/mariadb/mariadb.log
		INSTALL_CMD=cmake3
	fi

	if [ ! -f ${mysqlDir}/mysql-boost-${VERSION}.tar.gz ];then
		wget --no-check-certificate -O ${mysqlDir}/mysql-boost-${VERSION}.tar.gz --tries=3 https://cdn.mysql.com/archives/mysql-8.0/mysql-boost-${VERSION}.tar.gz
	fi

	#Periksa apakah file rusak.
	md5_mysql_ok=e0cb61cbf6e1144c452368c4535ae931
	if [ -f ${mysqlDir}/mysql-boost-${VERSION}.tar.gz ];then
		if [ "$sysName" == "Darwin" ];then
			md5_mysql=`md5 -q ${mysqlDir}/mysql-boost-${VERSION}.tar.gz`
		else
			md5_mysql=`md5sum ${mysqlDir}/mysql-boost-${VERSION}.tar.gz  | awk '{print $1}'`
		fi
		if [ "${md5_mysql_ok}" == "${md5_mysql}" ]; then
			echo "mysql8.0 file  check ok"
		else
			# Unduh ulang
			rm -rf ${mysqlDir}/mysql-${VERSION}
			wget --no-check-certificate -O ${mysqlDir}/mysql-boost-${VERSION}.tar.gz --tries=3 https://cdn.mysql.com/archives/mysql-8.0/mysql-boost-${VERSION}.tar.gz
		fi
	fi

	if [ ! -d ${mysqlDir}/mysql-${VERSION} ];then
		 cd ${mysqlDir} && tar -zxvf  ${mysqlDir}/mysql-boost-${VERSION}.tar.gz
	fi

	OPTIONS=''
	##check openssl version
	OPENSSL_VERSION=`openssl version|awk '{print $2}'|awk -F '.' '{print $1}'`
	if [ "${OPENSSL_VERSION}" -ge "3" ];then
		#openssl version to high
		cd ${rootPath}/plugins/php/lib && /bin/bash openssl.sh
		export PKG_CONFIG_PATH=$serverPath/lib/openssl/lib/pkgconfig
		OPTIONS="-DWITH_SSL=${serverPath}/lib/openssl"
	fi

	WHERE_DIR_GCC=/usr/bin/gcc
	WHERE_DIR_GPP=/usr/bin/g++
	if [ "$OSNAME" == "centos" ] && [ "$VERSION_ID" == "7" ];then
		echo "Fixing CentOS 7 repositories to use Vault..."
		sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/CentOS-*.repo
		sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-*.repo
		sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-*.repo

		yum install -y libudev-devel
		yum install -y centos-release-scl

		echo "Fixing CentOS SCL repositories to use Vault..."
		if [ -f /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo ]; then
			sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo
			sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo
			sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo
		fi
		if [ -f /etc/yum.repos.d/CentOS-SCLo-scl.repo ]; then
			sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/CentOS-SCLo-scl.repo
			sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-SCLo-scl.repo
			sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-SCLo-scl.repo
		fi

		yum install -y devtoolset-11-gcc devtoolset-11-gcc-c++ devtoolset-11-binutils

		gcc --version
		WHERE_DIR_GCC=/opt/rh/devtoolset-11/root/usr/bin/gcc
		WHERE_DIR_GPP=/opt/rh/devtoolset-11/root/usr/bin/g++
		echo $WHERE_DIR_GCC
		echo $WHERE_DIR_GPP
	fi

	if [ ! -f $WHERE_DIR_GCC ];then
		WHERE_DIR_GCC=`which gcc`
	fi

	if [ ! -f $WHERE_DIR_GPP ];then
		WHERE_DIR_GPP=`which g++`
	fi

	if [ ! -d $serverPath/mysql ];then
		cd ${mysqlDir}/mysql-${VERSION}
		# Clean up any previous in-source build files to avoid conflicts
		rm -rf CMakeCache.txt CMakeFiles Makefile cmake_install.cmake
		find . -name "CMakeCache.txt" -o -name "CMakeFiles" | xargs rm -rf
		
		if [ "$OSNAME" == "macos" ];then
			# Patch CMakeLists.txt for modern CMake
			find . -name "CMakeLists.txt" -o -name "*.cmake" | xargs sed -i '' 's/ OLD)/ NEW)/g'
			# Fix zlib fdopen conflict on macOS
			# Note: Path might be slightly different in 8.0
			ZLIB_H=$(find . -name "zutil.h" | grep "zlib-1.2.13")
			if [ -f "$ZLIB_H" ]; then
				sed -i '' 's/#        define fdopen(fd,mode) NULL \/\* No fdopen() \*\//#        if !defined(__APPLE__)\n#          define fdopen(fd,mode) NULL\n#        endif/g' "$ZLIB_H"
			fi
			
			rm -rf build
			mkdir build
			cd build
			cmake .. \
			-DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
			-DCMAKE_CXX_FLAGS="-Wno-enum-constexpr-conversion -Wno-deprecated-copy-with-user-provided-copy" \
			-DBISON_EXECUTABLE=/opt/homebrew/opt/bison/bin/bison \
			-DCMAKE_INSTALL_PREFIX=$serverPath/mysql \
			-DMYSQL_USER=mysql \
			-DMYSQL_TCP_PORT=3306 \
			-DMYSQL_UNIX_ADDR=/var/tmp/mysql.sock \
			-DWITH_MYISAM_STORAGE_ENGINE=1 \
			-DWITH_INNOBASE_STORAGE_ENGINE=1 \
			-DWITH_MEMORY_STORAGE_ENGINE=1 \
			-DENABLED_LOCAL_INFILE=1 \
			-DWITH_PARTITION_STORAGE_ENGINE=1 \
			-DEXTRA_CHARSETS=all \
			-DDEFAULT_CHARSET=utf8mb4 \
			-DDEFAULT_COLLATION=utf8mb4_general_ci \
			-DDOWNLOAD_BOOST=1 \
			-DENABLE_DOWNLOADS=1 \
			-DWITH_UNIT_TESTS=OFF \
			-DWITH_CURL=system \
			-DWITH_DEBUG=OFF \
			-DWITH_LIBEVENT=bundled \
			-DWITH_LZ4=bundled \
			-DWITH_ZLIB=bundled \
			-DWITH_ZSTD=bundled \
			-DWITH_FIDO=bundled \
			-DWITH_EDITLINE=system \
			-DWITH_ROUTER=OFF \
			-DWITH_X=OFF \
			-DCMAKE_OSX_ARCHITECTURES=arm64 \
			-DCMAKE_OSX_SYSROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk \
			-DCMAKE_DEPENDS_USE_COMPILER=OFF \
			-DABSL_PROPAGATE_CXX_STD=ON \
			$OPTIONS \
			-DCMAKE_C_COMPILER=${WHERE_DIR_GCC} \
			-DCMAKE_CXX_COMPILER=${WHERE_DIR_GPP} \
			-DWITH_BOOST=${mysqlDir}/mysql-${VERSION}/boost/
		else
			${INSTALL_CMD} \
			-DCMAKE_INSTALL_PREFIX=$serverPath/mysql \
			-DMYSQL_USER=mysql \
			-DMYSQL_TCP_PORT=3306 \
			-DMYSQL_UNIX_ADDR=/var/tmp/mysql.sock \
			-DWITH_MYISAM_STORAGE_ENGINE=1 \
			-DWITH_INNOBASE_STORAGE_ENGINE=1 \
			-DWITH_MEMORY_STORAGE_ENGINE=1 \
			-DENABLED_LOCAL_INFILE=1 \
			-DWITH_PARTITION_STORAGE_ENGINE=1 \
			-DWITH_READLINE=1 \
			-DEXTRA_CHARSETS=all \
			-DDEFAULT_CHARSET=utf8mb4 \
			-DDEFAULT_COLLATION=utf8mb4_general_ci \
			-DDOWNLOAD_BOOST=1 \
			-DFORCE_INSOURCE_BUILD=1 \
			$OPTIONS \
			-DCMAKE_C_COMPILER=$WHERE_DIR_GCC \
			-DCMAKE_CXX_COMPILER=$WHERE_DIR_GPP \
			-DWITH_BOOST=${mysqlDir}/mysql-${VERSION}/boost/
		fi
		
		make -j${cpuCore} && make install && make clean

		if [ -d $serverPath/mysql ];then
			rm -rf ${mysqlDir}/mysql-${VERSION}
			echo '8.0' > $serverPath/mysql/version.pl
			echo "${VERSION} Instalasi selesai"
		else
			# rm -rf ${mysqlDir}/mysql-${VERSION}
			echo "${VERSION} Instalasi gagal"
			exit 1
		fi
	fi
}

Uninstall_mysql()
{
	if [ -f $serverPath/mysql/init.d/mysql ];then
		$serverPath/mysql/init.d/mysql stop
	fi

	if [ -f /etc/init.d/mysql ];then
		rm -rf /etc/init.d/mysql
	fi

	rm -rf $serverPath/mysql
	echo 'Penghapusan selesai'
}

action=$1
if [ "${1}" == "install" ];then
	Install_mysql
else
	Uninstall_mysql
fi
