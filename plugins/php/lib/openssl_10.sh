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


if [ ! -d ${SERVER_ROOT}/openssl10 ] || [ ! -f ${SERVER_ROOT}/openssl10/include/openssl/evp.h ];then
    rm -rf ${SERVER_ROOT}/openssl10
    cd ${SOURCE_ROOT}

    if [ ! -f ${SOURCE_ROOT}/openssl-${opensslVersion}.tar.gz ];then
        wget --no-check-certificate -O openssl-${opensslVersion}.tar.gz https://github.com/midoks/panel/releases/download/init/openssl-${opensslVersion}.tar.gz -T 20
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


