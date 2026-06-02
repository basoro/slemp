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
SYS_ARCH=`arch`

version=7.4.33
PHP_VER=74
md5_file_ok=893d39589d81d6d841e067c2957f12e8

Install_php()
{
#------------------------ install start ------------------------------------#
echo "Menginstal php-${version} ..."
mkdir -p $sourcePath/php
mkdir -p $serverPath/php

# Clean up failed source code builds to avoid stale config cache
if [ -d $sourcePath/php/php${PHP_VER} ] && [ ! -d $serverPath/php/${PHP_VER} ]; then
	rm -rf $sourcePath/php/php${PHP_VER}
fi

cd ${rootPath}/plugins/php/lib && /bin/bash freetype_old.sh
cd ${rootPath}/plugins/php/lib && /bin/bash zlib.sh

if [ ! -d $sourcePath/php/php${PHP_VER} ];then
	
	cn=$(curl -fsSL -m 10 -s http://ipinfo.io/json | grep "\"country\": \"CN\"")
	LOCAL_ADDR=common
	if [ ! -z "$cn" ] || [ "$?" == "0" ] ;then
		LOCAL_ADDR=cn
	fi

	if [ "$LOCAL_ADDR" == "cn" ];then
		if [ ! -f $sourcePath/php/php-${version}.tar.xz ];then
			wget --no-check-certificate -O $sourcePath/php/php-${version}.tar.xz https://mirrors.nju.edu.cn/php/php-${version}.tar.xz
		fi
	fi

	if [ ! -f $sourcePath/php/php-${version}.tar.xz ];then
		wget --no-check-certificate -O $sourcePath/php/php-${version}.tar.xz https://museum.php.net/php7/php-${version}.tar.xz
	fi

	if [ -f $sourcePath/php/php-${version}.tar.xz ];then
		md5_file=`md5sum $sourcePath/php/php-${version}.tar.xz  | awk '{print $1}'`
		if [ "${md5_file}" != "${md5_file_ok}" ]; then
			echo "File unduhan PHP${version} tidak lengkap, instal ulang"
			rm -rf $sourcePath/php/php-${version}.tar.xz
		fi
	fi
	
	cd $sourcePath/php && tar -Jxf $sourcePath/php/php-${version}.tar.xz
	mv $sourcePath/php/php-${version} $sourcePath/php/php${PHP_VER}
fi

OPTIONS='--without-iconv'
if [ $sysName == 'Darwin' ]; then
	OPTIONS="${OPTIONS} --with-freetype-dir=${serverPath}/lib/freetype"
else
	OPTIONS="${OPTIONS} --with-readline"
fi

IS_64BIT=`getconf LONG_BIT`
if [ "$IS_64BIT" == "64" ] && [ "$sysName" != "Darwin" ];then
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

if [ "${SYS_ARCH}" == "arm64" ] && [ "$sysName" == "Darwin" ] ;then
	PATCH_PATH=${rootPath}/plugins/php/versions/${PHP_VER}/src
	[ -f ${PATCH_PATH}/ext/pcre/sljitConfigInternal.h ] && cp -f ${PATCH_PATH}/ext/pcre/sljitConfigInternal.h $sourcePath/php/php${PHP_VER}/ext/pcre/pcrelib/sljit/sljitConfigInternal.h
	[ -f ${PATCH_PATH}/reentrancy.c ] && cp -f ${PATCH_PATH}/reentrancy.c $sourcePath/php/php${PHP_VER}/main/reentrancy.c
	[ -f ${PATCH_PATH}/mkstemp.c ] && cp -f ${PATCH_PATH}/mkstemp.c $sourcePath/php/php${PHP_VER}/ext/zip/lib/mkstemp.c
	
	[ -f $sourcePath/php/php${PHP_VER}/ext/pcre/pcrelib/sljit/sljitConfigInternal.h ] && sed -i '' 's/defined (__aarch64__)/defined (__aarch64__) || defined(__arm64__)/g' $sourcePath/php/php${PHP_VER}/ext/pcre/pcrelib/sljit/sljitConfigInternal.h
	[ -f $sourcePath/php/php${PHP_VER}/ext/pcre/pcrelib/sljit/sljitConfig.h ] && sed -i '' 's/\/\* #define SLJIT_CONFIG_AUTO 1 \*\//#define SLJIT_CONFIG_AUTO 1/g' $sourcePath/php/php${PHP_VER}/ext/pcre/pcrelib/sljit/sljitConfig.h
	[ -f $sourcePath/php/php${PHP_VER}/ext/dom/dom_iterators.c ] && sed -i '' 's/void \*payload, void \*data, xmlChar \*name/void \*payload, void \*data, const xmlChar \*name/g' $sourcePath/php/php${PHP_VER}/ext/dom/dom_iterators.c
	[ -f $sourcePath/php/php${PHP_VER}/ext/pdo_sqlite/sqlite_statement.c ] && sed -i '' 's/zend_ulong \*len/unsigned long \*len/g' $sourcePath/php/php${PHP_VER}/ext/pdo_sqlite/sqlite_statement.c
	[ -f $sourcePath/php/php${PHP_VER}/ext/libxml/libxml.c ] && sed -i '' 's/void \*userData, xmlErrorPtr error/void \*userData, const xmlError \*error/g' $sourcePath/php/php${PHP_VER}/ext/libxml/libxml.c
	[ -f $sourcePath/php/php${PHP_VER}/ext/libxml/libxml.c ] && sed -i '' 's/int compression ATTRIBUTE_UNUSED/int compression/g' $sourcePath/php/php${PHP_VER}/ext/libxml/libxml.c
fi

if [ "$sysName" == "Darwin" ];then
	cd ${rootPath}/plugins/php/lib && /bin/bash openssl_11.sh
	OPENSSL_11_DIR=${serverPath}/lib/openssl11
	OPTIONS="$OPTIONS --with-openssl=${OPENSSL_11_DIR}"
	export PKG_CONFIG_PATH=${OPENSSL_11_DIR}/lib/pkgconfig
	export OPENSSL_CFLAGS="-I${OPENSSL_11_DIR}/include"
	export OPENSSL_LIBS="-L${OPENSSL_11_DIR}/lib -lssl -lcrypto -lz"
	export CPPFLAGS="-I${OPENSSL_11_DIR}/include -I$(brew --prefix zlib)/include"
	export LDFLAGS="-L${OPENSSL_11_DIR}/lib -L$(brew --prefix zlib)/lib -lresolv"
	export LIBS="-lresolv -lz"
	OPTIONS="$OPTIONS --with-zlib=$(brew --prefix zlib) --without-pcre-jit"

	if brew list oniguruma > /dev/null 2>&1; then
		OPTIONS="$OPTIONS --with-onig=$(brew --prefix oniguruma)"
	fi
	if brew list libxml2 > /dev/null 2>&1; then
		OPTIONS="$OPTIONS --with-libxml-dir=$(brew --prefix libxml2)"
	fi
else
	if [ -f /usr/include/openssl/evp.h ] && ! openssl version 2>&1 | grep -qE "OpenSSL (3\.|[4-9]\.)"; then
		OPTIONS="$OPTIONS --with-openssl"
	else
		cd ${rootPath}/plugins/php/lib && /bin/bash openssl_11.sh
		OPENSSL_11_DIR=${serverPath}/lib/openssl11
		if [ -d ${OPENSSL_11_DIR}/lib64 ] && [ ! -d ${OPENSSL_11_DIR}/lib ]; then
			ln -sf ${OPENSSL_11_DIR}/lib64 ${OPENSSL_11_DIR}/lib
		elif [ -d ${OPENSSL_11_DIR}/lib64 ] && [ -d ${OPENSSL_11_DIR}/lib ]; then
			cp -fr ${OPENSSL_11_DIR}/lib64/* ${OPENSSL_11_DIR}/lib/
		fi
		export PKG_CONFIG_PATH=${OPENSSL_11_DIR}/lib/pkgconfig:$PKG_CONFIG_PATH
		export OPENSSL_CFLAGS="-I${OPENSSL_11_DIR}/include"
		export OPENSSL_LIBS="-L${OPENSSL_11_DIR}/lib -L${OPENSSL_11_DIR}/lib64 -lssl -lcrypto -lz -Wl,-rpath,${OPENSSL_11_DIR}/lib -Wl,-rpath,${OPENSSL_11_DIR}/lib64"
		export CPPFLAGS="-I${OPENSSL_11_DIR}/include"
		export LDFLAGS="-L${OPENSSL_11_DIR}/lib -L${OPENSSL_11_DIR}/lib64 -Wl,-rpath,${OPENSSL_11_DIR}/lib -Wl,-rpath,${OPENSSL_11_DIR}/lib64"
		OPTIONS="$OPTIONS --with-openssl=${OPENSSL_11_DIR}"
	fi
fi

if [ ! -d $serverPath/php/${PHP_VER} ];then
	if [ "$sysName" != "Darwin" ]; then
		export CFLAGS="-w -O2 -fPIC -Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types -Wno-error=int-conversion -Wno-error=implicit-int -Wno-error=return-type"
		export CXXFLAGS="-w -O2 -fPIC -Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types -Wno-error=int-conversion -Wno-error=implicit-int -Wno-error=return-type"
	fi

	cd $sourcePath/php/php${PHP_VER} && ./configure \
	--prefix=$serverPath/php/${PHP_VER} \
	--exec-prefix=$serverPath/php/${PHP_VER} \
	--with-config-file-path=$serverPath/php/${PHP_VER}/etc \
	--enable-mysqlnd \
	--with-mysql=mysqlnd \
	--with-mysqli=mysqlnd \
	--with-pdo-mysql=mysqlnd \
	--enable-mbstring \
	--enable-simplexml \
	--enable-ftp \
	--enable-sockets \
	--enable-soap \
	--enable-posix \
	--enable-sysvmsg \
	--enable-sysvsem \
	--enable-sysvshm \
	--disable-intl \
	--disable-fileinfo \
	$OPTIONS \
	--enable-fpm
	make clean && make -j${cpuCore} && make install && make clean
fi
#------------------------ install end ------------------------------------#
}

Uninstall_php()
{
	$serverPath/php/init.d/php74 stop
	rm -rf $serverPath/php/74
	echo "Menghapus instalasi php-${version} ..."
}

action=${1}
if [ "${1}" == 'install' ];then
	Install_php
else
	Uninstall_php
fi
