#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")
rootPath=$(dirname "$rootPath")

# echo $rootPath

SERVER_ROOT=$rootPath/lib
SOURCE_ROOT=$rootPath/source/lib

HTTP_PREFIX="https://"

if [ ! -d ${SERVER_ROOT}/curl ];then

    cd $SOURCE_ROOT
    if [ ! -f ${SOURCE_ROOT}/curl-7.88.1.tar.gz ];then
        wget --no-check-certificate -O curl-7.88.1.tar.gz ${HTTP_PREFIX}github.com/curl/curl/releases/download/curl-7_88_1/curl-7.88.1.tar.gz -T 20
    fi

    tar -zxvf curl-7.88.1.tar.gz
    cd curl-7.88.1

    ./configure --prefix=${SERVER_ROOT}/curl --with-openssl && make && make install

    #cd $SOURCE_ROOT
    #rm -rf curl-7.88.1
    #rm -rf curl-7.88.1.tar.gz
fi
