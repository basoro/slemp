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

version=${3:-8.1.34}
PHP_VER=81
IS_UPDATE=${PHP_UPDATE:-0}
INSTALL_ROOT_PATH=${PHP_INSTALL_ROOT:-}

php2shellGetSha256()
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
			8.1.34) sha="ffa9e0982e82eeaea848f57687b425ed173aa278fe563001310ae2638db5c251" ;;
			8.1.33) sha="9db83bf4590375562bc1a10b353cccbcf9fcfc56c58b7c8fb814e6865bb928d1" ;;
		esac
	fi
	echo "${sha}"
}

php2shellGetPatch()
{
	local info_file="${rootPath}/plugins/php/info.json"
	local patch=""
	if [ -f "${info_file}" ] && command -v python3 >/dev/null 2>&1; then
		patch=$(python3 - "$info_file" "$PHP_VER" "$version" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    updates = data.get('updates', {})
    item = updates.get(sys.argv[2], {}) if isinstance(updates, dict) else {}
    if isinstance(item, dict) and item.get('version') == sys.argv[3]:
        print(item.get('patch', ''))
    else:
        print('')
except Exception:
    print('')
PY
)
	fi
	if [ -n "${patch}" ] && [ -f "${rootPath}/plugins/php/patches/${patch}" ]; then
		echo "${rootPath}/plugins/php/patches/${patch}"
	fi
}

md5_file_ok=$(php2shellGetSha256)
if [ -z "${md5_file_ok}" ]; then
	echo "Checksum PHP ${version} tidak tersedia, instalasi dibatalkan."
	exit 1
fi
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

cd ${rootPath}/plugins/php/lib && /bin/bash freetype_new.sh
cd ${rootPath}/plugins/php/lib && /bin/bash zlib.sh

# redat ge 8
which yum
if [ "$?" == "0" ];then
	cd ${rootPath}/plugins/php/lib && /bin/bash oniguruma.sh
fi

patched=0
if [ "${IS_UPDATE}" == "1" ];then
	rm -rf $sourcePath/php/php${PHP_VER}
fi

if [ ! -d $sourcePath/php/php${PHP_VER} ];then

	# ----------------------------------------------------------------------- #
	# Instalasi dengan optimasi Tiongkok
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
	# ----------------------------------------------------------------------- #

	if [ ! -f $sourcePath/php/php-${version}.tar.xz ];then
		wget --no-check-certificate -O $sourcePath/php/php-${version}.tar.xz https://www.php.net/distributions/php-${version}.tar.xz
	fi
		
	#Periksa apakah file rusak.
	if [ ! -f $sourcePath/php/php-${version}.tar.xz ];then
		echo "Gagal mengunduh PHP ${version}."
		exit 1
	fi

	md5_file=`sha256sum $sourcePath/php/php-${version}.tar.xz  | awk '{print $1}'`
	if [ "${md5_file}" != "${md5_file_ok}" ]; then
		echo "Checksum PHP ${version} tidak cocok, instalasi dibatalkan."
		rm -rf $sourcePath/php/php-${version}.tar.xz
		exit 1
	fi

	cd $sourcePath/php && tar -Jxf $sourcePath/php/php-${version}.tar.xz
	if [ ! -d $sourcePath/php/php-${version} ];then
		echo "Ekstraksi PHP ${version} gagal."
		exit 1
	fi
	rm -rf $sourcePath/php/php${PHP_VER}
	mv $sourcePath/php/php-${version} $sourcePath/php/php${PHP_VER}

	patchFile="${PHP_PATCH_FILE:-$(php2shellGetPatch)}"
	if [ -n "${patchFile}" ] && [ -f "${patchFile}" ];then
		echo "Menerapkan patch PHP2Shell pada PHP ${version} ..."
		cd $sourcePath/php/php${PHP_VER}
		patch -p1 --batch --forward < "${patchFile}" || exit 1
		patched=1
	fi
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

echo "$sourcePath/php/php${PHP_VER}"

if [ "$sysName" == "Darwin" ];then
	BREW_DIR=`which brew`
	BREW_DIR=${BREW_DIR/\/bin\/brew/}

	LIB_DEPEND_DIR=`brew info openssl | grep ${BREW_DIR}/Cellar/openssl | cut -d \  -f 1 | awk 'END {print}'`
	OPTIONS="$OPTIONS --with-openssl=$(brew --prefix openssl)"
	export PKG_CONFIG_PATH=$LIB_DEPEND_DIR/lib/pkgconfig
	export OPENSSL_CFLAGS="-I${LIB_DEPEND_DIR}/include"
	export OPENSSL_LIBS="-L/${LIB_DEPEND_DIR}/lib -lssl -lcrypto -lz"
else
	cd ${rootPath}/plugins/php/lib && /bin/bash openssl_11.sh
	OPENSSL_11_DIR=${serverPath}/lib/openssl11
	if [ -d ${OPENSSL_11_DIR}/lib64 ] && [ ! -d ${OPENSSL_11_DIR}/lib ]; then
		ln -sf ${OPENSSL_11_DIR}/lib64 ${OPENSSL_11_DIR}/lib
	elif [ -d ${OPENSSL_11_DIR}/lib64 ] && [ -d ${OPENSSL_11_DIR}/lib ]; then
		cp -fr ${OPENSSL_11_DIR}/lib64/* ${OPENSSL_11_DIR}/lib/
	fi
	if [ -d ${OPENSSL_11_DIR}/lib ] && [ ! -d ${OPENSSL_11_DIR}/lib64 ]; then
		ln -sf lib ${OPENSSL_11_DIR}/lib64
	fi
	export PKG_CONFIG_PATH=${OPENSSL_11_DIR}/lib/pkgconfig:$PKG_CONFIG_PATH
	export OPENSSL_CFLAGS="-I${OPENSSL_11_DIR}/include"
	export OPENSSL_LIBS="-L${OPENSSL_11_DIR}/lib -L${OPENSSL_11_DIR}/lib64 -lssl -lcrypto -lz -ldl -Wl,-rpath,${OPENSSL_11_DIR}/lib -Wl,-rpath,${OPENSSL_11_DIR}/lib64"
	export CPPFLAGS="-I${OPENSSL_11_DIR}/include -Wno-error"
	export LDFLAGS="-L${OPENSSL_11_DIR}/lib -L${OPENSSL_11_DIR}/lib64 -ldl -Wl,-rpath,${OPENSSL_11_DIR}/lib -Wl,-rpath,${OPENSSL_11_DIR}/lib64"
	OPTIONS="$OPTIONS --with-openssl=${OPENSSL_11_DIR}"

	if [ -f /usr/bin/yum ]; then
		libxml_ver=$(pkg-config --modversion libxml-2.0 2>/dev/null)
		if [ "$?" != "0" ] || [ "$(printf '%s\n' "2.9.4" "$libxml_ver" | sort -V | head -n1)" != "2.9.4" ]; then
			cd ${rootPath}/plugins/php/lib && /bin/bash libxml2.sh
			export PKG_CONFIG_PATH=${serverPath}/lib/libxml2/lib/pkgconfig:$PKG_CONFIG_PATH
		fi
	fi
fi

if [ "${IS_UPDATE}" == "1" ] || [ ! -d $serverPath/php/${PHP_VER} ];then
	if [ "$sysName" != "Darwin" ]; then
		export CFLAGS="-w -O2 -fPIC -Wno-error"
		export CXXFLAGS="-w -O2 -fPIC -Wno-error"
	fi
	cd $sourcePath/php/php${PHP_VER}
	./configure \
	--prefix=$serverPath/php/${PHP_VER} \
	--exec-prefix=$serverPath/php/${PHP_VER} \
	--with-config-file-path=$serverPath/php/${PHP_VER}/etc \
	--enable-mysqlnd \
	--with-mysql=mysqlnd \
	--with-mysqli=mysqlnd \
	--with-pdo-mysql=mysqlnd \
	--enable-ftp \
	--enable-mbstring \
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
		if [ "${patched}" == "1" ];then
			touch $serverPath/php/${PHP_VER}/.php2shell_patched
		fi
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
