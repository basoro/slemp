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
mkdir -p $SOURCE_ROOT

HTTP_PREFIX="https://"
cn=$(curl -fsSL -m 10 -s http://ipinfo.io/json | grep "\"country\": \"CN\"")
if [ ! -z "$cn" ]; then
    HTTP_PREFIX="https://mirror.ghproxy.com/"
fi

if [ ! -f ${SERVER_ROOT}/oniguruma/lib/libonig.a ];then
    cd ${SOURCE_ROOT}
    if [ ! -f ${SOURCE_ROOT}/oniguruma-6.9.4.tar.gz ];then
        wget --no-check-certificate -O ${SOURCE_ROOT}/oniguruma-6.9.4.tar.gz ${HTTP_PREFIX}github.com/kkos/oniguruma/archive/v6.9.4.tar.gz
    fi

    if [ ! -d ${SOURCE_ROOT}/oniguruma-6.9.4 ];then
        cd ${SOURCE_ROOT} && tar -zxvf oniguruma-6.9.4.tar.gz
    fi
    
    cd ${SOURCE_ROOT}/oniguruma-6.9.4
    if [ "$(uname)" == "Darwin" ];then
        ./autogen.sh
        ./configure --prefix=${SERVER_ROOT}/oniguruma --host=arm-apple-darwin
    else
        ./autogen.sh
        ./configure --prefix=${SERVER_ROOT}/oniguruma
    fi
    make -j${cpuCore} && make install
    cd $SOURCE_ROOT && rm -rf $SOURCE_ROOT/oniguruma-6.9.4
fi

if [ -d ${SERVER_ROOT}/oniguruma ]; then
    export ONIG_CFLAGS="-I${SERVER_ROOT}/oniguruma/include"
    export ONIG_LIBS="-L${SERVER_ROOT}/oniguruma/lib -lonig"
fi

