#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin

curPath=`pwd`
rootPath=$(dirname "$curPath")


echo $rootPath
cd $rootPath
rm -rf ./*.pyc
rm -rf ./*/*.pyc

startTime=`date +%s`

zip -r -q -o slemp.zip  ./ -x@$curPath/pick_filter.txt



mv slemp.zip $rootPath/scripts

endTime=`date +%s`
((outTime=($endTime-$startTime)))
echo -e "Time consumed:\033[32m $outTime \033[0mSec!"
