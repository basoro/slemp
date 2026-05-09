#!/bin/bash
PANEL_DIR=$(cd "$(dirname "$0")/../.."; pwd)

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:/opt/homebrew/bin:~/bin
export PATH
LANG=en_US.UTF-8

echo 'The development environment only needs to be downloaded again!'
exit 0