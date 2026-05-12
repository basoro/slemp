#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

if [ -z "$rootPath" ]; then
    DIR=$(cd "$(dirname "$0")"; pwd)
    rootPath=$(dirname "$(dirname "$(dirname "$(dirname "$DIR")")")")
    serverPath=$(dirname "$rootPath")
fi

sysName=`uname`
action=$1
type=$2

VERSION=1.25.3.2

openrestyDir=${serverPath}/source/openresty

Install_openresty()
{
	if [ "${action}" == "install" ];then
		if [ -d $serverPath/openresty ];then
			exit 0
		fi
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

	mkdir -p ${openrestyDir}
	echo 'Sedang menginstal file skrip...'

	# wget -O openresty-1.21.4.1.tar.gz https://openresty.org/download/openresty-1.21.4.1.tar.gz
	if [ ! -f ${openrestyDir}/openresty-${VERSION}.tar.gz ];then
		wget --no-check-certificate -O ${openrestyDir}/openresty-${VERSION}.tar.gz https://openresty.org/download/openresty-${VERSION}.tar.gz -T 30
	fi

	DOWNLOAD_SIZE=`wc -c ${openrestyDir}/openresty-${VERSION}.tar.gz | awk '{print $1}'`
	if [ "$DOWNLOAD_SIZE" == "0" ];then
		echo 'Failed to download OpenResty source tarball!'
		rm -rf ${openrestyDir}/openresty-${VERSION}.tar.gz
		exit 1
	fi

	cd ${openrestyDir} && tar -zxvf openresty-${VERSION}.tar.gz

	OPTIONS=''

	opensslVersion="3.4.4"
	libresslVersion="3.9.1"
	pcreVersion='8.45'
	if [ "$sysName" == "Darwin" ];then

		if [ ! -f ${openrestyDir}/pcre-${pcreVersion}.tar.gz ];then
			wget --no-check-certificate -O ${openrestyDir}/pcre-${pcreVersion}.tar.gz https://netix.dl.sourceforge.net/project/pcre/pcre/${pcreVersion}/pcre-${pcreVersion}.tar.gz
		fi

		if [ ! -d ${openrestyDir}/pcre-${pcreVersion} ];then
			cd ${openrestyDir} &&  tar -zxvf pcre-${pcreVersion}.tar.gz
		fi
		OPTIONS="${OPTIONS} --with-pcre=${openrestyDir}/pcre-${pcreVersion}"


		if [ ! -f ${openrestyDir}/openssl-${opensslVersion}.tar.gz ];then
	        wget --no-check-certificate -O ${openrestyDir}/openssl-${opensslVersion}.tar.gz https://www.openssl.org/source/openssl-${opensslVersion}.tar.gz
	    fi

	    if [ ! -d ${openrestyDir}/openssl-${opensslVersion} ];then
			cd ${openrestyDir} &&  tar -zxvf openssl-${opensslVersion}.tar.gz
		fi
	    OPTIONS="${OPTIONS} --with-openssl=${openrestyDir}/openssl-${opensslVersion}"

		# BREW_DIR=`which brew`
		# BREW_DIR=${BREW_DIR/\/bin\/brew/}

		# brew info openssl@1.1 | grep /opt/homebrew/Cellar/openssl@1.1 | cut -d \  -f 1 | awk 'END {print}'
		# OPENSSL_LIB_DEPEND_DIR=`brew info openssl@1.1 | grep ${BREW_DIR}/Cellar/openssl@1.1 | cut -d \  -f 1 | awk 'END {print}'`
		# OPTIONS="${OPTIONS} --with-openssl=${OPENSSL_LIB_DEPEND_DIR}"
	else
		if [ ! -f ${openrestyDir}/pcre-${pcreVersion}.tar.gz ];then
			wget --no-check-certificate -O ${openrestyDir}/pcre-${pcreVersion}.tar.gz https://netix.dl.sourceforge.net/project/pcre/pcre/${pcreVersion}/pcre-${pcreVersion}.tar.gz
		fi

		if [ ! -d ${openrestyDir}/pcre-${pcreVersion} ];then
			cd ${openrestyDir} &&  tar -zxvf pcre-${pcreVersion}.tar.gz
		fi
		OPTIONS="${OPTIONS} --with-pcre=${openrestyDir}/pcre-${pcreVersion}"
		
		if [ ! -f ${openrestyDir}/openssl-${opensslVersion}.tar.gz ];then
	        wget --no-check-certificate -O ${openrestyDir}/openssl-${opensslVersion}.tar.gz https://www.openssl.org/source/openssl-${opensslVersion}.tar.gz
	    fi

	    if [ ! -d ${openrestyDir}/openssl-${opensslVersion} ];then
			cd ${openrestyDir} &&  tar -zxvf openssl-${opensslVersion}.tar.gz
		fi
		OPTIONS="${OPTIONS} --with-openssl=${openrestyDir}/openssl-${opensslVersion}"

	fi

	if [[ "$VERSION" =~ "1.25.3" ]]; then
		OPTIONS="${OPTIONS} --with-http_v3_module"

		# if [ ! -f ${openrestyDir}/libressl-${libresslVersion}.tar.gz ];then
	    #     wget --no-check-certificate -O ${openrestyDir}/libressl-${libresslVersion}.tar.gz https://ftp.openbsd.org/pub/OpenBSD/LibreSSL/libressl-${libresslVersion}.tar.gz
	    # fi

	    # if [ ! -d ${openrestyDir}/libressl-${libresslVersion} ];then
		# 	cd ${openrestyDir} &&  tar -zxvf libressl-${libresslVersion}.tar.gz
		# fi
	    
	    # OPTIONS="${OPTIONS} --with-cc-opt=-I${openrestyDir}/libressl-${libresslVersion}/libressl/build/include"
	    # OPTIONS="${OPTIONS} --with-cc-opt=-I${openrestyDir}/libressl-${libresslVersion}/libressl/build/lib"
	fi

	# br
	if [ ! -d ${openrestyDir}/ngx_brotli ];then
		cd ${openrestyDir} && git clone https://github.com/wxx9248/ngx_brotli.git
		cd ${openrestyDir}/ngx_brotli && git submodule update --init
		if [ "$sysName" == "Darwin" ];then
			cd ${openrestyDir}/ngx_brotli/deps/brotli
			mkdir -p out && cd out
			cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF ..
			cmake --build . --config Release --target brotlienc
		fi
	fi
	OPTIONS="${OPTIONS} --add-module=${openrestyDir}/ngx_brotli"

	OPTIONS="${OPTIONS} --with-threads"
	OPTIONS="${OPTIONS} --with-pcre-jit"
	OPTIONS="${OPTIONS} --with-http_gzip_static_module"

	if [ "$sysName" != "Darwin" ];then
		OPTIONS="${OPTIONS} --with-file-aio"
	fi

	if [ ! -d ${openrestyDir}/zstd-nginx-module-master ];then
		cd ${openrestyDir} && wget -O $openrestyDir/zstd-nginx-module.tar.gz https://github.com/tokers/zstd-nginx-module/archive/refs/heads/master.tar.gz
		
	if [ ! -f ${openrestyDir}/openresty-${VERSION}.tar.gz ]; then
		echo "Failed to download OpenResty source tarball!"
		exit 1
	fi

	cd ${openrestyDir} && tar -zxvf zstd-nginx-module.tar.gz

		if [ "$sysName" == "Darwin" ];then
			export ZSTD_INC=/opt/homebrew/include
			export ZSTD_LIB=/opt/homebrew/lib
		fi

		pkg-config --exists --print-errors libzstd
		if [ "$?" == "0" ];then
			OPTIONS="${OPTIONS} --add-module=${openrestyDir}/zstd-nginx-module-master"
		fi
	fi

	cd ${openrestyDir}/openresty-${VERSION} && ./configure \
	--prefix=$serverPath/openresty \
	$OPTIONS \
	--with-stream \
	--with-http_v2_module \
	--with-http_ssl_module  \
	--with-http_slice_module \
	--with-http_stub_status_module \
	--with-http_sub_module \
	--with-http_realip_module
	# --without-luajit-gc64
	# --with-debug
	# Digunakan untuk debugging

	CMD_MAKE=`which gmake`
	if [ "$?" == "0" ];then
		gmake -j${cpuCore} && gmake install && gmake clean
	else
		make -j${cpuCore} && make install && make clean
	fi


    if [ -d ${openrestyDir}/pcre-${pcreVersion} ];then
    	rm -rf ${openrestyDir}/pcre-${pcreVersion}
    fi

    if [ -d ${openrestyDir}/openssl-${opensslVersion} ];then
    	rm -rf ${openrestyDir}/openssl-${opensslVersion}
    fi

    if [ -d ${openrestyDir}/libressl-${libresslVersion} ];then
    	rm -rf ${openrestyDir}/libressl-${libresslVersion}
    fi

    if [ -f $serverPath/openresty/bin/openresty ];then
		if [ -d $openrestyDir/openresty-${VERSION} ];then
			rm -rf $openrestyDir/openresty-${VERSION}
		fi
		echo 'Instalasi selesai'
	else
		echo 'Instalasi gagal'
		exit 1
	fi
}

Uninstall_openresty()
{
	echo 'Penghapusan instalasi selesai'
}

action=$1
if [ "${1}" == "install" ];then
	Install_openresty
elif [ "${1}" == "upgrade" ];then
	Install_openresty
else
	Uninstall_openresty
fi
