#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

DIR=$(cd "$(dirname "$0")"; pwd)
curPath=$DIR
# rootPath = panel directory (parent of plugins)
# DIR: .../plugins/ollama/versions/1.0
# dirname(DIR): .../plugins/ollama/versions
# dirname(dirname(DIR)): .../plugins/ollama
# dirname(dirname(dirname(DIR))): .../plugins
# dirname(dirname(dirname(dirname(DIR)))): .../panel (correct!)
rootPath=$(dirname "$(dirname "$(dirname "$(dirname "$DIR")")")")
serverPath=$(dirname "$rootPath")
pluginPath=$rootPath/plugins/ollama

VERSION=1.0
sysName=`uname`
sysArch=`arch`

get_python() {
	if [ "$sysName" == "Darwin" ]; then
		PYTHON=/usr/bin/python3
	elif [ -x /usr/bin/python3 ]; then
		PYTHON=/usr/bin/python3
	elif [ -x /bin/python3 ]; then
		PYTHON=/bin/python3
	elif [ -x /usr/local/bin/python3 ]; then
		PYTHON=/usr/local/bin/python3
	elif command -v python3 &> /dev/null; then
		PYTHON=$(command -v python3)
	else
		PYTHON=python3
	fi
}

get_arch() {
	if [ "$sysArch" == "x86_64" ];then
		ARCH="amd64"
	elif [ "$sysArch" == "aarch64" ] || [ "$sysArch" == "arm64" ];then
		ARCH="arm64"
	else
		ARCH="amd64"
	fi
}

Install_App()
{
	get_python
	get_arch

	echo "[1/3] Mengunduh Ollama..."

	if [ "$sysName" == "Darwin" ]; then
		# macOS - use official install script
		curl -fSLs https://ollama.com/install.sh | sh
	else
		# Linux - use official install script
		curl -fSLs https://ollama.com/install.sh | sh

		# Create systemd service for Linux
		if [ ! -f /etc/systemd/system/ollama.service ]; then
			cat > /etc/systemd/system/ollama.service << EOF
[Unit]
Description=Ollama Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ollama serve
User=root
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
			systemctl daemon-reload
			systemctl enable ollama
		fi
	fi

	echo "[2/3] Konfigurasi..."
	mkdir -p $serverPath/ollama
	echo "$VERSION" > $serverPath/ollama/version.pl

	echo "[3/3] Memulai service..."
	cd ${rootPath} && $PYTHON ${pluginPath}/index.py start
	echo 'Instalasi berhasil'
}

Uninstall_App()
{
	get_python

	cd ${rootPath} && $PYTHON ${pluginPath}/index.py stop

	if [ "$sysName" == "Darwin" ]; then
		if command -v brew &> /dev/null; then
			brew uninstall ollama 2>/dev/null
		fi
		ollama stop 2>/dev/null
		rm -rf $(which ollama) 2>/dev/null
		rm -rf /usr/local/bin/ollama 2>/dev/null
		rm -rf /opt/homebrew/bin/ollama 2>/dev/null
		rm -rf /Applications/Ollama.app 2>/dev/null
		rm -rf ~/.ollama 2>/dev/null
	else
		systemctl stop ollama 2>/dev/null
		systemctl disable ollama 2>/dev/null
		rm -rf /etc/systemd/system/ollama.service 2>/dev/null
		systemctl daemon-reload
		rm -rf $(which ollama) 2>/dev/null
		rm -rf /usr/local/bin/ollama 2>/dev/null
		rm -rf /usr/share/ollama 2>/dev/null
		rm -rf ~/.ollama 2>/dev/null
	fi

	rm -rf $serverPath/ollama
	echo 'Penghapusan berhasil'
}

action=$1
if [ "${1}" == 'install' ];then
	Install_App
else
	Uninstall_App
fi
