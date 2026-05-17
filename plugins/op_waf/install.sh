#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH

# cd /www/server/panel/plugins/op_waf && bash install.sh install 0.4.1
# cd /www/server/panel && python3 plugins/op_waf/index.py start
# cd /www/server/panel && python3 plugins/op_waf/index.py stop
# cd /www/server/panel && python3 plugins/op_waf/tool_task.py run

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
rootPath=$(dirname "$(dirname "$DIR")")
serverPath=$(dirname "$rootPath")
export rootPath
export serverPath

action=$1
version=$2
sys_os=`uname`

if [ -f ${rootPath}/bin/activate ];then
	source ${rootPath}/bin/activate
elif [ -f $(dirname "$serverPath")/bin/activate ];then
	source $(dirname "$serverPath")/bin/activate
fi

if [ "$sys_os" == "Darwin" ];then
	BAK='_bak'
else
	BAK=''
fi

# /www/server/openresty/luajit/bin/luajit /www/server/op_waf/waf/lua/waf_common.lua
# /www/server/openresty/luajit/bin/luajit -bl /www/server/op_waf/waf/lua/waf_common.lua
# /www/server/openresty/luajit/bin/luajit /www/server/web_conf/nginx/lua/access_by_lua_file.lua


Install_App(){
	
	echo 'Sedang menginstal file skrip...'
	mkdir -p $serverPath/source/op_waf
	mkdir -p $serverPath/op_waf

	# luarocks
	if [ ! -f $serverPath/source/op_waf/luarocks-3.5.0.tar.gz ];then
		wget --no-check-certificate -O $serverPath/source/op_waf/luarocks-3.5.0.tar.gz http://luarocks.org/releases/luarocks-3.5.0.tar.gz
	fi
	
	# which luarocks
	if [ ! -d $serverPath/op_waf/luarocks ];then
		cd $serverPath/source/op_waf && tar xvf luarocks-3.5.0.tar.gz
		# cd luarocks-3.9.1 && ./configure && make bootstrap

		cd luarocks-3.5.0 && ./configure --prefix=$serverPath/op_waf/luarocks \
		--with-lua-include=$serverPath/openresty/luajit/include/luajit-2.1 \
		--with-lua-bin=$serverPath/openresty/luajit/bin
		make -I${serverPath}/openresty/luajit/bin
		make install 
	fi


	if [ ! -f $serverPath/source/op_waf/lsqlite3_v096.zip ];then
		wget --no-check-certificate -O $serverPath/source/op_waf/lsqlite3_v096.zip http://lua.sqlite.org/home/zip/lsqlite3_v096.zip?uuid=v0.9.6
	fi

	if [ ! -d $serverPath/source/op_waf/lsqlite3_v096 ];then
		cd $serverPath/source/op_waf && unzip lsqlite3_v096.zip
	fi

	PATH=${serverPath}/openresty/luajit:${serverPath}/openresty/luajit/include/luajit-2.1:$PATH
	export PATH=$PATH:$serverPath/op_waf/luarocks/bin

	if [ ! -f $serverPath/op_waf/waf/conf/lsqlite3.so ];then
		if [ "${sys_os}" == "Darwin" ];then
			cd $serverPath/source/op_waf/lsqlite3_v096
			LIB_SQLITE_DIR=`brew --prefix sqlite`
			echo "SQLite path: $LIB_SQLITE_DIR"
			sed -i $BAK "s#SQLITE_DIR=#SQLITE_DIR=${LIB_SQLITE_DIR}#g" Makefile
			make
		else
			cd $serverPath/source/op_waf/lsqlite3_v096
			gcc -O2 -shared -fPIC -o lsqlite3.so lsqlite3.c -I$serverPath/openresty/luajit/include/luajit-2.1 -lsqlite3
		fi
	fi

	# copy to code path
	mkdir -p $serverPath/op_waf/waf/conf
	if [ -f $serverPath/source/op_waf/lsqlite3_v096/lsqlite3.so ];then
		cp -rf $serverPath/source/op_waf/lsqlite3_v096/lsqlite3.so $serverPath/op_waf/waf/conf/lsqlite3.so
	elif [ -f $serverPath/op_waf/luarocks/lib/lua/5.1/lsqlite3.so ];then
		cp -rf $serverPath/op_waf/luarocks/lib/lua/5.1/lsqlite3.so $serverPath/op_waf/waf/conf/lsqlite3.so
	fi

	cn=$(curl -fsSL -m 10 http://ipinfo.io/json | grep "\"country\": \"CN\"")
	HTTP_PREFIX="https://"
	if [ ! -z "$cn" ];then
	    HTTP_PREFIX="https://gh-proxy.com/"
	fi

	# download GeoLite Data
	GeoLite2_TAG=`curl -sL "https://api.github.com/repos/P3TERX/GeoLite.mmdb/releases/latest" | grep '"tag_name":' | cut -d'"' -f4`
	if [ ! -f $serverPath/source/op_waf/GeoLite2-City.mmdb ];then
		wget --no-check-certificate -O $serverPath/source/op_waf/GeoLite2-City.mmdb ${HTTP_PREFIX}github.com/P3TERX/GeoLite.mmdb/releases/download/${GeoLite2_TAG}/GeoLite2-City.mmdb
	fi

	if [ ! -f $serverPath/op_waf/GeoLite2-City.mmdb ];then
		cp -rf $serverPath/source/op_waf/GeoLite2-City.mmdb $serverPath/op_waf/GeoLite2-City.mmdb
	fi

	if [ ! -f $serverPath/source/op_waf/GeoLite2-Country.mmdb ];then
		wget --no-check-certificate -O $serverPath/source/op_waf/GeoLite2-Country.mmdb ${HTTP_PREFIX}github.com/P3TERX/GeoLite.mmdb/releases/download/${GeoLite2_TAG}/GeoLite2-Country.mmdb
	fi

	if [ ! -f $serverPath/op_waf/GeoLite2-Country.mmdb ];then
		cp -rf $serverPath/source/op_waf/GeoLite2-Country.mmdb $serverPath/op_waf/GeoLite2-Country.mmdb
	fi


	libmaxminddb_ver='1.12.2'
	if [ ! -f $serverPath/op_waf/waf/mmdb/lib/libmaxminddb.a ] && [ ! -f $serverPath/op_waf/waf/mmdb/lib/libmaxminddb.so ];then
		libmaxminddb_local_path=$serverPath/source/op_waf/libmaxminddb-${libmaxminddb_ver}.tar.gz
		libmaxminddb_url_path=${HTTP_PREFIX}github.com/maxmind/libmaxminddb/releases/download/${libmaxminddb_ver}/libmaxminddb-${libmaxminddb_ver}.tar.gz
		if [ ! -f ${libmaxminddb_local_path} ]; then
			wget --no-check-certificate -O ${libmaxminddb_local_path} ${libmaxminddb_url_path}
		fi

		cd $serverPath/source/op_waf && tar -zxvf ${libmaxminddb_local_path} && \
		cd $serverPath/source/op_waf/libmaxminddb-${libmaxminddb_ver} && \
		./configure --prefix=$serverPath/op_waf/waf/mmdb && make && make install
	fi

	# Install geoip2 python library
	if [ -f ${rootPath}/bin/pip ];then
		${rootPath}/bin/pip install geoip2
	else
		pip install geoip2
	fi

	echo "${version}" > $serverPath/op_waf/version.pl
	echo 'Instalasi Firewall WAF berhasil!'

	cd ${rootPath} && python3 ${rootPath}/plugins/op_waf/index.py start
	echo "cd ${rootPath} && python3 ${rootPath}/plugins/op_waf/index.py start"
	sleep 2
	cd ${rootPath} && python3 ${rootPath}/plugins/op_waf/index.py reload
}

Uninstall_App(){
	cd ${rootPath} && python3 ${rootPath}/plugins/op_waf/index.py stop
	if [ "$?" == "0" ];then
		rm -rf $serverPath/op_waf
	fi
}


action=$1
if [ "${1}" == 'install' ];then
	Install_App
else
	Uninstall_App
fi
