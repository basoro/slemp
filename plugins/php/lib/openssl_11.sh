#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

opensslVersion="1.1.1w"
SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib
mkdir -p $SOURCE_ROOT

if [ ! -d ${SERVER_ROOT}/openssl11 ];then
    cd ${SOURCE_ROOT}
    DOWNLOAD_SUCCESS=false
    if [ -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz ]; then
        DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz | awk '{print $1}'`
        if [ "$DOWNLOAD_SIZE" -gt "1000000" ]; then
            DOWNLOAD_SUCCESS=true
        else
            rm -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz
        fi
    fi

    # Try downloading from official old archive
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading OpenSSL ${opensslVersion} from official OpenSSL archive..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz https://www.openssl.org/source/old/1.1.1/openssl-${opensslVersion}.tar.gz -T 30
        if [ -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "1000000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    fi

    # Try standard source directory
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading from standard OpenSSL source directory..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz https://www.openssl.org/source/openssl-${opensslVersion}.tar.gz -T 30
        if [ -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "1000000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    fi

    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Failed to download OpenSSL ${opensslVersion} source tarball!"
        exit 1
    fi

    tar -zxvf openssl-${opensslVersion}.tar.gz
    cd openssl-${opensslVersion}
    
    if [ "$(uname)" == "Darwin" ];then
        ./Configure darwin64-arm64-cc --prefix=${SERVER_ROOT}/openssl11 zlib-dynamic shared
    else
        export CFLAGS="-w -fPIC -O2"
        ./config --prefix=${SERVER_ROOT}/openssl11 zlib-dynamic shared
    fi
    
    make && make install
    
    if [ "$(uname)" != "Darwin" ];then
        if [ -d /etc/ld.so.conf.d ];then
            echo "${SERVER_ROOT}/openssl11/lib" > /etc/ld.so.conf.d/openssl11.conf
            echo "${SERVER_ROOT}/openssl11/lib64" >> /etc/ld.so.conf.d/openssl11.conf
        elif [ -f /etc/ld.so.conf ]; then
            echo "${SERVER_ROOT}/openssl11/lib" >> /etc/ld.so.conf
            echo "${SERVER_ROOT}/openssl11/lib64" >> /etc/ld.so.conf
        fi
        ldconfig
    fi

    cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/openssl-${opensslVersion}
fi

