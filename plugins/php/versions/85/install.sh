#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH=$PATH:/opt/homebrew/bin

if [ -z "$rootPath" ]; then
    DIR=$(cd "$(dirname "$0")"; pwd)
    rootPath=$(dirname "$(dirname "$(dirname "$(dirname "$DIR")")")")
    serverPath=$(dirname "$rootPath")
fi
sourcePath=${serverPath}/source
sysName=`uname`

version=${3:-8.5.12}
PHP_VER=85
IS_UPDATE=${PHP_UPDATE:-0}
INSTALL_ROOT_PATH=${PHP_INSTALL_ROOT:-}

getSha256()
{
	local info_file="${rootPath}/plugins/php/info.json"
	local sha=""
	if [ -f "${info_file}" ] && command -v python3 >/dev/null 2>&1; then
		sha=$(python3 - "$info_file" "$PHP_VER" "$version" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    updates = data.get('updates', {})
    item = updates.get(sys.argv[2], {}) if isinstance(updates, dict) else {}
    if isinstance(item, dict) and item.get('version') == sys.argv[3]:
        print(item.get('sha256', ''))
    else:
        print('')
except Exception:
    print('')
PY
)
	fi

	if [ -z "${sha}" ]; then
		case "${version}" in
			8.5.12) sha="08bc2eba2a588654ade1357174aa646b761556c862dda0678345ee29ed481209" ;;
			8.5.5) sha="95bec382f4bd00570a8ef52a58ec04d8d9b9a90494781f1c106d1b274a3902f2" ;;
		esac
	fi

	echo "${sha}"
}

md5_file_ok=$(getSha256)
if [ -z "${md5_file_ok}" ]; then
	echo "Checksum PHP ${version} tidak tersedia, instalasi dibatalkan."
	exit 1
fi

Download_php()
{
	local tar_file=$sourcePath/php/php-${version}.tar.xz

	if [ ! -f $tar_file ];then
		# ----------------------------------------------------------------------- #
		# Instalasi dengan optimasi Tiongkok
		cn=$(curl -fsSL -m 10 -s http://ipinfo.io/json | grep "\"country\": \"CN\"")
		LOCAL_ADDR=common
		if [ ! -z "$cn" ];then
			LOCAL_ADDR=cn
		fi

		if [ "$LOCAL_ADDR" == "cn" ];then
			wget --no-check-certificate -O $tar_file https://mirrors.nju.edu.cn/php/php-${version}.tar.xz
		fi
		# ----------------------------------------------------------------------- #

		if [ ! -f $tar_file ];then
			wget --no-check-certificate -O $tar_file https://www.php.net/distributions/php-${version}.tar.xz
			# wget --no-check-certificate -O $tar_file https://downloads.php.net/~edorian/php-${version}.tar.xz
		fi
	fi

	#Periksa apakah file rusak.
	if [ ! -f $tar_file ];then
		echo "Gagal mengunduh PHP ${version}."
		return 1
	fi

	local sha_file=`sha256sum $tar_file | awk '{print $1}'`
	if [ "${sha_file}" != "${md5_file_ok}" ]; then
		echo "File unduhan PHP${version} tidak lengkap, unduh ulang"
		rm -f $tar_file
		wget --no-check-certificate -O $tar_file https://www.php.net/distributions/php-${version}.tar.xz
		sha_file=`sha256sum $tar_file | awk '{print $1}'`
		if [ "${sha_file}" != "${md5_file_ok}" ]; then
			echo "Checksum PHP ${version} tidak cocok, instalasi dibatalkan."
			rm -f $tar_file
			return 1
		fi
	fi

	return 0
}

Install_php()
{
#------------------------ install start ------------------------------------#
echo "Menginstal php-${version} ..."
mkdir -p $sourcePath/php
mkdir -p $serverPath/php

cd ${rootPath}/plugins/php/lib && /bin/bash freetype_new.sh
cd ${rootPath}/plugins/php/lib && /bin/bash zlib.sh

# redat ge 8
which yum
if [ "$?" == "0" ];then
	cd ${rootPath}/plugins/php/lib && /bin/bash oniguruma.sh
fi

# Saat update, source lama harus diganti dengan source versi target.
if [ "${IS_UPDATE}" == "1" ];then
	rm -rf $sourcePath/php/php${PHP_VER}
fi

if [ ! -d $sourcePath/php/php${PHP_VER} ];then
	Download_php || exit 1

	cd $sourcePath/php && tar -Jxf $sourcePath/php/php-${version}.tar.xz
	if [ ! -d $sourcePath/php/php-${version} ];then
		echo "Ekstraksi PHP ${version} gagal."
		exit 1
	fi
	rm -rf $sourcePath/php/php${PHP_VER}
	mv $sourcePath/php/php-${version} $sourcePath/php/php${PHP_VER}
fi

cd $sourcePath/php/php${PHP_VER}

OPTIONS='--without-iconv'

# if [ $sysName == 'Darwin' ]; then
# 	OPTIONS="${OPTIONS} --with-curl"
# fi

argon_version=`pkg-config libargon2 --modversion`
if [ "$?" == "0" ];then
	OPTIONS="${OPTIONS} --with-password-argon2"
fi

IS_64BIT=`getconf LONG_BIT`
if [ "$IS_64BIT" == "64" ];then
	OPTIONS="${OPTIONS} --with-libdir=lib64"
fi

# ----- cpu start ------
if [ -z "${cpuCore}" ]; then
	cpuCore="1"
fi

if [ -f /proc/cpuinfo ];then
	cpuCore=`cat /proc/cpuinfo | grep "processor" | wc -l`
fi

MEM_INFO=$(which free > /dev/null && free -m|grep Mem|awk '{printf("%.f",($2)/1024)}')
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

# OPTIONS="${OPTIONS} --enable-debug"
# OPTIONS="${OPTIONS} --enable-dtrace"

if [ "$sysName" == "Darwin" ];then
	BREW_DIR=`which brew`
	BREW_DIR=${BREW_DIR/\/bin\/brew/}

	LIB_DEPEND_DIR=`brew info openssl | grep ${BREW_DIR}/Cellar/openssl | cut -d \  -f 1 | awk 'END {print}'`
	OPTIONS="$OPTIONS --with-openssl=$(brew --prefix openssl)"
	export PKG_CONFIG_PATH=$LIB_DEPEND_DIR/lib/pkgconfig
	export OPENSSL_CFLAGS="-I${LIB_DEPEND_DIR}/include"
	export OPENSSL_LIBS="-L/${LIB_DEPEND_DIR}/lib -lssl -lcrypto -lz"
else
	echo "lib"
	cd ${rootPath}/plugins/php/lib && /bin/bash openssl_11.sh
	export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:$serverPath/lib/openssl11/lib/pkgconfig
	OPTIONS="$OPTIONS --with-openssl=$serverPath/lib/openssl11"

	if [ -f /usr/bin/yum ]; then
		libxml_ver=$(pkg-config --modversion libxml-2.0 2>/dev/null)
		if [ "$?" != "0" ] || [ "$(printf '%s\n' "2.9.4" "$libxml_ver" | sort -V | head -n1)" != "2.9.4" ]; then
			cd ${rootPath}/plugins/php/lib && /bin/bash libxml2.sh
			export PKG_CONFIG_PATH=${serverPath}/lib/libxml2/lib/pkgconfig:$PKG_CONFIG_PATH
		fi

		zlib_ver=$(pkg-config --modversion zlib 2>/dev/null)
		if [ "$?" != "0" ] || [ "$(printf '%s\n' "1.2.11" "$zlib_ver" | sort -V | head -n1)" != "1.2.11" ]; then
			cd ${rootPath}/plugins/php/lib && /bin/bash zlib.sh
			export PKG_CONFIG_PATH=${serverPath}/lib/zlib/lib/pkgconfig:$PKG_CONFIG_PATH
		fi
	fi
fi

echo "$sourcePath/php/php${PHP_VER}"

if [ "${IS_UPDATE}" == "1" ] || [ ! -d $serverPath/php/${PHP_VER} ];then
	cd $sourcePath/php/php${PHP_VER}
	# ./buildconf --force
	./configure \
	--prefix=$serverPath/php/${PHP_VER} \
	--exec-prefix=$serverPath/php/${PHP_VER} \
	--with-config-file-path=$serverPath/php/${PHP_VER}/etc \
	--enable-mysqlnd \
	--with-mysql=mysqlnd \
	--with-mysqli=mysqlnd \
	--with-pdo-mysql=mysqlnd \
	--with-mysqlnd-ssl \
	--enable-mbstring \
	--enable-ftp \
	--enable-sockets \
	--enable-simplexml \
	--enable-soap \
	--enable-posix \
	--enable-sysvmsg \
	--enable-sysvsem \
	--enable-sysvshm \
	--disable-intl \
	--disable-fileinfo \
	$OPTIONS \
	--enable-fpm || exit 1

	make clean && make -j${cpuCore} || exit 1
	if [ -n "${INSTALL_ROOT_PATH}" ];then
		make install INSTALL_ROOT=${INSTALL_ROOT_PATH} || exit 1
	else
		make install || exit 1
	fi
	make clean

	if [ -z "${INSTALL_ROOT_PATH}" ];then
		echo "${version}" > $serverPath/php/${PHP_VER}/version.pl
	fi

	# rm -rf $sourcePath/php/php${PHP_VER}
fi
#------------------------ install end ------------------------------------#
}

Uninstall_php()
{
	$serverPath/php/init.d/php${PHP_VER} stop
	rm -rf $serverPath/php/${PHP_VER}
	echo "Menghapus instalasi php-${version}..."
}

action=${1}
if [ "${1}" == 'install' ];then
	Install_php
else
	Uninstall_php
fi
