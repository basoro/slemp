#!/usr/bin/env bash
set -e

# Path detection
curPath=`pwd`
rootPath=$(dirname "$curPath")
serverPath=$(dirname "$rootPath")/server
libPath=$serverPath/lib
sourcePath=$serverPath/source/lib

PREFIX="$libPath"
BUILD="$sourcePath"
DEPS="$PREFIX"

CPU=$(sysctl -n hw.ncpu 2>/dev/null || nproc)

mkdir -p "$PREFIX" "$BUILD" "$PREFIX/logs" "$PREFIX/run"

########################################
# TOOLCHAIN (WAJIB – FIX ICU / C++)
########################################
export CC=clang
export CXX=clang++
export CFLAGS="-O2 -fPIC -I$DEPS/include"
export CXXFLAGS="-O2 -fPIC -std=c++17 -I$DEPS/include -Wno-enum-constexpr-conversion -Wno-deprecated-declarations"
export LDFLAGS="-L$DEPS/lib -lc++"

########################################
# PKG-CONFIG (STABIL – JANGAN DIOVERWRITE)
########################################
export PATH="$DEPS/bin:/usr/bin:/bin"
export PKG_CONFIG="$DEPS/bin/pkg-config"
export PKG_CONFIG_PATH="$DEPS/lib/pkgconfig"
export PKG_CONFIG_LIBDIR="$DEPS/lib/pkgconfig"

########################################
# HELPER
########################################
download() {
  cd "$BUILD"
  local url="$1"
  local file="${url##*/}"
  [ -f "$file" ] || curl -L -O "$url"
}

########################################
# pkgconf (pkg-config replacement)
########################################
echo "Installing pkgconf..."
download https://distfiles.dereferenced.org/pkgconf/pkgconf-2.2.0.tar.xz
rm -rf pkgconf-2.2.0 && tar xf pkgconf-2.2.0.tar.xz
cd pkgconf-2.2.0
./configure --prefix="$DEPS"
make -j$CPU && make install
ln -sf "$DEPS/bin/pkgconf" "$DEPS/bin/pkg-config"

########################################
# zlib
########################################
echo "Installing zlib..."
download https://zlib.net/zlib-1.3.1.tar.gz
rm -rf zlib-1.3.1 && tar xf zlib-1.3.1.tar.gz
cd zlib-1.3.1
./configure --prefix="$DEPS"
make -j$CPU && make install

########################################
# OpenSSL
########################################
echo "Installing OpenSSL..."
download https://www.openssl.org/source/openssl-3.2.1.tar.gz
rm -rf openssl-3.2.1 && tar xf openssl-3.2.1.tar.gz
cd openssl-3.2.1
./Configure --prefix="$DEPS" no-shared
make -j$CPU && make install_sw

########################################
# libiconv
########################################
echo "Installing libiconv..."
download https://ftp.gnu.org/pub/gnu/libiconv/libiconv-1.17.tar.gz
rm -rf libiconv-1.17 && tar xf libiconv-1.17.tar.gz
cd libiconv-1.17
./configure --prefix="$DEPS" --enable-static --disable-shared
make -j$CPU && make install

########################################
# oniguruma
########################################
echo "Installing oniguruma..."
download https://github.com/kkos/oniguruma/releases/download/v6.9.9/onig-6.9.9.tar.gz
rm -rf onig-6.9.9 && tar xf onig-6.9.9.tar.gz
cd onig-6.9.9
./configure --prefix="$DEPS" --disable-shared --enable-static
make -j$CPU && make install

########################################
# ICU (PHP intl, FIX C++)
########################################
echo "Installing ICU..."
download https://github.com/unicode-org/icu/releases/download/release-74-2/icu4c-74_2-src.tgz
rm -rf icu && tar xf icu4c-74_2-src.tgz
cd icu/source
./configure --prefix="$DEPS" --disable-shared --enable-static
make -j$CPU && make install

########################################
# SQLite
########################################
echo "Installing SQLite..."
download https://www.sqlite.org/2024/sqlite-autoconf-3450200.tar.gz
rm -rf sqlite-autoconf-3450200 && tar xf sqlite-autoconf-3450200.tar.gz
cd sqlite-autoconf-3450200
./configure --prefix="$DEPS"
make -j$CPU && make install

########################################
# libunistring
########################################
echo "Installing libunistring..."
download https://ftp.gnu.org/gnu/libunistring/libunistring-1.2.tar.gz
rm -rf libunistring-1.2 && tar xf libunistring-1.2.tar.gz
cd libunistring-1.2
./configure --prefix="$DEPS" --disable-shared --enable-static
make -j$CPU && make install

########################################
# libidn2
########################################
echo "Installing libidn2..."
download https://ftp.gnu.org/gnu/libidn/libidn2-2.3.7.tar.gz
rm -rf libidn2-2.3.7 && tar xf libidn2-2.3.7.tar.gz
cd libidn2-2.3.7
./configure \
  --prefix="$DEPS" \
  --with-libunistring-prefix="$DEPS" \
  --without-included-unistring \
  --disable-shared \
  --enable-static \
  --disable-glib
make -j$CPU && make install

########################################
# curl
########################################
echo "Installing curl..."
download https://curl.se/download/curl-8.6.0.tar.gz
rm -rf curl-8.6.0 && tar xf curl-8.6.0.tar.gz
cd curl-8.6.0
# Disable pkg-config temporarily to force using our built openssl/idn2
OLD_PKG_CONFIG=$PKG_CONFIG
export PKG_CONFIG=/bin/false
./configure \
  --prefix="$DEPS" \
  --with-openssl="$DEPS" \
  --with-libidn2="$DEPS" \
  --without-libpsl \
  --disable-psl
make -j$CPU && make install
export PKG_CONFIG=$OLD_PKG_CONFIG

########################################
# PCRE2 (REQUIRED FOR NGINX)
########################################
echo "Installing PCRE2..."
download https://github.com/PCRE2Project/pcre2/releases/download/pcre2-10.43/pcre2-10.43.tar.gz
rm -rf pcre2-10.43 && tar xf pcre2-10.43.tar.gz
cd pcre2-10.43
./configure --prefix="$DEPS" --disable-shared --enable-static
make -j$CPU && make install

########################################
# libxml2 (REQUIRED FOR PHP)
########################################
echo "Installing libxml2..."
download https://download.gnome.org/sources/libxml2/2.12/libxml2-2.12.5.tar.xz
rm -rf libxml2-2.12.5 && tar xf libxml2-2.12.5.tar.xz
cd libxml2-2.12.5
./configure --prefix="$DEPS" --disable-shared --enable-static --without-python --without-lzma --without-zstd
make -j$CPU && make install

########################################
# M4 (REQUIRED FOR BISON)
########################################
echo "Installing M4..."
download https://ftp.gnu.org/gnu/m4/m4-1.4.19.tar.gz
rm -rf m4-1.4.19 && tar xf m4-1.4.19.tar.gz
cd m4-1.4.19
./configure --prefix="$DEPS"
make -j$CPU && make install

########################################
# BISON (WAJIB UNTUK MYSQL)
########################################
echo "Installing Bison..."
download https://ftp.gnu.org/gnu/bison/bison-3.8.2.tar.gz
rm -rf bison-3.8.2 && tar xf bison-3.8.2.tar.gz
cd bison-3.8.2
./configure --prefix="$DEPS"
make -j$CPU && make install

########################################
# RE2C (REQUIRED FOR PHP/MYSQL)
########################################
echo "Installing re2c..."
download https://github.com/skvadrik/re2c/releases/download/3.1/re2c-3.1.tar.xz
rm -rf re2c-3.1 && tar xf re2c-3.1.tar.xz
cd re2c-3.1
./configure --prefix="$DEPS"
make -j$CPU && make install

########################################
# CMake (REQUIRED FOR MYSQL)
########################################
echo "Installing CMake..."
download https://github.com/Kitware/CMake/releases/download/v3.29.2/cmake-3.29.2.tar.gz
rm -rf cmake-3.29.2 && tar xf cmake-3.29.2.tar.gz
cd cmake-3.29.2
./bootstrap --prefix="$DEPS" -- -DCMAKE_USE_SYSTEM_ZLIB=ON
make -j$CPU && make install

echo "All core libraries installed successfully in $PREFIX"
