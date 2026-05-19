#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

opensslVersion="1.0.2q"
# echo $rootPath

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib

mkdir -p ${SERVER_ROOT}
mkdir -p ${SOURCE_ROOT}

if [ ! -d ${SERVER_ROOT}/openssl10 ] || [ ! -f ${SERVER_ROOT}/openssl10/include/openssl/evp.h ];then
    rm -rf ${SERVER_ROOT}/openssl10
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

    # Try downloading from official archive first
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading OpenSSL 1.0.2q from official OpenSSL archive..."
        wget --no-check-certificate -O ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz https://www.openssl.org/source/old/1.0.2/openssl-${opensslVersion}.tar.gz -T 30
        if [ -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz ]; then
            DOWNLOAD_SIZE=`wc -c ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz | awk '{print $1}'`
            if [ "$DOWNLOAD_SIZE" -gt "1000000" ]; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    fi

    # Fallback to GitHub releases URL
    if [ "$DOWNLOAD_SUCCESS" = false ]; then
        echo "Downloading from fallback GitHub releases..."
        rm -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz
        wget --no-check-certificate -O ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz https://github.com/midoks/panel/releases/download/init/openssl-${opensslVersion}.tar.gz -T 30
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

    tar -zxf openssl-${opensslVersion}.tar.gz
    cd openssl-${opensslVersion}
    ./config --prefix=${SERVER_ROOT}/openssl10 --openssldir=${SERVER_ROOT}/openssl10 zlib-dynamic shared
    make && make install

    # export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${serverPath}/lib/openssl10/lib
    if [ -d /etc/ld.so.conf.d ];then
        echo "${serverPath}/lib/openssl10/lib" > /etc/ld.so.conf.d/openssl10.conf
    elif [ -f /etc/ld.so.conf ]; then
        echo "${serverPath}/lib/openssl10/lib" >> /etc/ld.so.conf
    fi

    ldconfig
    # ldconfig -p  | grep openssl

    cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/openssl-${opensslVersion}
fi


