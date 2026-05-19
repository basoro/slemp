#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

# echo $rootPath

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib

mkdir -p  $SOURCE_ROOT

if [ ! -d ${SERVER_ROOT}/zlib ];then
    cd $SOURCE_ROOT

    DOWNLOAD_SUCCESS=false
    if [ -f ${SOURCE_ROOT}/zlib-1.2.11.tar.gz ]; then
        DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/zlib-1.2.11.tar.gz | awk '{print $1}'`
        if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
            DOWNLOAD_SUCCESS=true
        else
            rm -f ${SOURCE_ROOT}/zlib-1.2.11.tar.gz
        fi
    fi

    # Try downloading from official fossils archive
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading zlib 1.2.11 from official fossils archive..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/zlib-1.2.11.tar.gz https://zlib.net/fossils/zlib-1.2.11.tar.gz -T 30
        if [ -f ${SOURCE_ROOT}/zlib-1.2.11.tar.gz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/zlib-1.2.11.tar.gz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    fi

    # Try downloading from GitHub fallback
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading zlib 1.2.11 from GitHub fallback..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/zlib-1.2.11.tar.gz https://github.com/madler/zlib/archive/v1.2.11.tar.gz -T 30
        if [ -f ${SOURCE_ROOT}/zlib-1.2.11.tar.gz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/zlib-1.2.11.tar.gz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "500000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    fi

    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Failed to download zlib!"
        exit 1
    fi

    if [ ! -d ${SOURCE_ROOT}/zlib-1.2.11 ];then
        cd $SOURCE_ROOT && tar -zxvf zlib-1.2.11.tar.gz
    fi

    cd ${SOURCE_ROOT}/zlib-1.2.11
    ./configure --prefix=${SERVER_ROOT}/zlib && make && make install

    cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/zlib-1.2.11
fi