#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib
mkdir -p $SERVER_ROOT
mkdir -p $SOURCE_ROOT

libxmlVersion="2.9.10"

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

if [ ! -d ${SERVER_ROOT}/libxml2 ] || [ ! -f ${SERVER_ROOT}/libxml2/include/libxml2/libxml/xmlversion.h ];then
    rm -rf ${SERVER_ROOT}/libxml2
    cd ${SOURCE_ROOT}

    DOWNLOAD_SUCCESS=false
    if [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz ]; then
        DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz | awk '{print $1}'`
        if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
            DOWNLOAD_SUCCESS=true
        else
            rm -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz
        fi
    fi

    if [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz ] && [ "$DOWNLOAD_SUCCESS" = false ]; then
        DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz | awk '{print $1}'`
        if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
            DOWNLOAD_SUCCESS=true
        else
            rm -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz
        fi
    fi

    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading libxml2 ${libxmlVersion} from GNOME official source..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz https://download.gnome.org/sources/libxml2/2.9/libxml2-${libxmlVersion}.tar.xz -T 30
        if [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
        
        if [ "$DOWNLOAD_SUCCESS" = false ]; then
            echo "GNOME official source download failed. Trying fallback GitHub release..."
            rm -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz
            wget --no-check-certificate -O ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz https://github.com/GNOME/libxml2/archive/refs/tags/v${libxmlVersion}.tar.gz -T 30
            if [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz ]; then
                DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz | awk '{print $1}'`
                if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
                    DOWNLOAD_SUCCESS=true
                fi
            fi
        fi
    fi

    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Failed to download libxml2!"
        exit 1
    fi

    if [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.xz ]; then
        tar -Jxf libxml2-${libxmlVersion}.tar.xz
    elif [ -f ${SOURCE_ROOT}/libxml2-${libxmlVersion}.tar.gz ]; then
        tar -zxf libxml2-${libxmlVersion}.tar.gz
    fi

    cd libxml2-${libxmlVersion}
    ./configure --prefix=${SERVER_ROOT}/libxml2 --without-python --without-lzma --with-zlib
    make -j${cpuCore} && make install
    
    if [ "$?" == "0" ];then
        cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/libxml2-${libxmlVersion}
    fi
fi
