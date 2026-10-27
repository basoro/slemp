#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin:/opt/homebrew/bin
export PATH=$PATH:/opt/homebrew/bin

DIR=$(cd "$(dirname "$0")"; pwd)
if [ -z "$rootPath" ]; then
	rootPath=$(dirname "$(dirname "$DIR")")
	serverPath=$(dirname "$rootPath")
fi
export rootPath
export serverPath

PHP_VER=$1
target=$2
pluginDir=${rootPath}/plugins/php
phpDir=${serverPath}/php/${PHP_VER}
sourcePath=${serverPath}/source/php
stageDir=${sourcePath}/stage${PHP_VER}
backupDir=${rootPath}/data/backup
phpIni=${phpDir}/etc/php.ini

backupFile=""
iniBackup=""
oldModules=""
newModules=""
oldSo=""
extDir=""

log()
{
	echo "[php-update] $*"
}

abort()
{
	log "GAGAL: $*"
	exit 1
}

rollback()
{
	log "Mengembalikan instalasi PHP ${PHP_VER} dari backup..."
	if command -v python3 >/dev/null 2>&1; then
		(cd "$rootPath" && python3 "$pluginDir/index.py" stop "$PHP_VER" >/dev/null 2>&1)
	fi
	systemctl stop php${PHP_VER} >/dev/null 2>&1

	if [ -n "$backupFile" ] && [ -f "$backupFile" ]; then
		rm -rf "$phpDir"
		tar -xzf "$backupFile" -C "$(dirname "$phpDir")" || log "PERINGATAN: restore backup gagal, cek manual ${backupFile}"
		rm -f "$phpDir/var/run/php-fpm.pid"
	else
		log "PERINGATAN: file backup tidak ditemukan."
	fi

	if [ -n "$iniBackup" ] && [ -f "$iniBackup" ]; then
		cp -f "$iniBackup" "$phpIni"
	fi

	rm -rf "$stageDir"

	if command -v python3 >/dev/null 2>&1; then
		(cd "$rootPath" && python3 "$pluginDir/index.py" start "$PHP_VER" >/dev/null 2>&1)
	fi
	log "Rollback selesai."
}

fail()
{
	log "GAGAL: $*"
	rollback
	exit 1
}

getPhpVersion()
{
	"$1" -r 'echo PHP_VERSION;' 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -n1
}

listPhpModules()
{
	"$1" -m 2>/dev/null | grep -vE '^(PHP )?(Warning|Deprecated|Notice|Fatal error)' | grep -E '^[A-Za-z]' | sort -u
}

getPatchFile()
{
	local info_file="${pluginDir}/info.json"
	local patch=""
	if [ -f "${info_file}" ] && command -v python3 >/dev/null 2>&1; then
		patch=$(python3 - "$info_file" "$PHP_VER" "$target" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    updates = data.get('updates', {})
    item = updates.get(sys.argv[2], {}) if isinstance(updates, dict) else {}
    if isinstance(item, dict) and item.get('version') == sys.argv[3]:
        print(item.get('patch', ''))
    else:
        print('')
except Exception:
    print('')
PY
)
	fi
	echo "${patch}"
}

getSha256()
{
	local info_file="${pluginDir}/info.json"
	local sha=""
	if [ -f "${info_file}" ] && command -v python3 >/dev/null 2>&1; then
		sha=$(python3 - "$info_file" "$PHP_VER" "$target" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    updates = data.get('updates', {})
    item = updates.get(sys.argv[2], {}) if isinstance(updates, dict) else {}
    if isinstance(item, dict) and item.get('version') == sys.argv[3]:
        print(item.get('sha256', ''))
    else:
        print('')
except Exception:
    print('')
PY
)
	fi
	echo "${sha}"
}

rebuildExtension()
{
	local so="$1"
	local name="${so%.so}"
	local script="${rootPath}/plugins/php/versions/common/${name}.sh"

	if [ ! -f "$script" ]; then
		log "Script rebuild untuk ekstensi ${name} tidak tersedia."
		return 1
	fi

	local saved=$(mktemp)
	grep -E "^[[:space:]]*extension[[:space:]]*=[[:space:]]*${name}\.so" "$phpIni" > "$saved" 2>/dev/null
	sed -i -E "/^[[:space:]]*extension[[:space:]]*=[[:space:]]*${name}\.so/d" "$phpIni"

	(cd "${rootPath}/plugins/php/versions/common" && bash "$script" install "$PHP_VER") || true

	sed -i -E "/^[[:space:]]*extension[[:space:]]*=[[:space:]]*${name}\.so/d" "$phpIni"
	cat "$saved" >> "$phpIni"
	rm -f "$saved"

	[ -f "${extDir}/${so}" ]
}

# ------------------------------ preflight ------------------------------ #
if [ -z "$PHP_VER" ] || [ -z "$target" ]; then
	abort "Parameter update tidak lengkap."
fi

echo "$PHP_VER" | grep -Eq '^[0-9]{2}$' || abort "Branch PHP tidak valid: ${PHP_VER}"
echo "$target" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || abort "Versi target tidak valid: ${target}"

if [ ! -f "$pluginDir/versions/${PHP_VER}/install.sh" ]; then
	abort "Branch PHP ${PHP_VER} tidak mendukung fitur update."
fi

if [ ! -x "$phpDir/bin/php" ]; then
	abort "PHP ${PHP_VER} belum terpasang di ${phpDir}."
fi

installed=$(getPhpVersion "$phpDir/bin/php")
echo "$installed" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || abort "Versi PHP terpasang tidak dapat dideteksi."

patchFile=$(getPatchFile)
patchPath=""
if [ -n "$patchFile" ]; then
	patchPath="${pluginDir}/patches/${patchFile}"
	if [ ! -f "$patchPath" ]; then
		abort "File patch ${patchFile} tidak ditemukan."
	fi
	export PHP_PATCH_FILE="$patchPath"
fi

if [ "$installed" == "$target" ]; then
	if [ -z "$patchFile" ] || [ -f "$phpDir/.php2shell_patched" ]; then
		abort "PHP ${PHP_VER} sudah berada pada versi ${target}."
	fi
fi

newest=$(printf '%s\n%s\n' "$installed" "$target" | sort -V | tail -n1)
if [ "$newest" != "$target" ]; then
	abort "Versi target ${target} lebih lama dari versi terpasang ${installed}."
fi

sha256_target=$(getSha256)
if [ -z "$sha256_target" ] && [ -z "$patchFile" ]; then
	abort "Tidak ada patch keamanan untuk branch PHP ${PHP_VER} (EOL). Migrasikan ke PHP 8.2 atau lebih baru."
fi
if [ -z "$sha256_target" ]; then
	abort "Checksum PHP ${target} tidak tersedia di info.json."
fi

availKb=$(df -Pk "$serverPath" | awk 'NR==2 {print $4}')
if [ -z "$availKb" ] || [ "$availKb" -lt 3145728 ]; then
	abort "Ruang disk tidak cukup (butuh minimal 3 GB, tersedia $(( ${availKb:-0} / 1024 )) MB)."
fi

mkdir -p "$sourcePath" || abort "Tidak dapat membuat direktori source."
tarFile="$sourcePath/php-${target}.tar.xz"
if [ ! -f "$tarFile" ]; then
	log "Mengunduh sumber PHP ${target}..."
	cn=$(curl -fsSL -m 10 -s http://ipinfo.io/json | grep '"country": "CN"')
	if [ -n "$cn" ]; then
		wget --no-check-certificate -O "$tarFile" "https://mirrors.nju.edu.cn/php/php-${target}.tar.xz" >/dev/null 2>&1 || true
	fi
	if [ ! -f "$tarFile" ]; then
		wget --no-check-certificate -O "$tarFile" "https://www.php.net/distributions/php-${target}.tar.xz" || abort "Gagal mengunduh PHP ${target}."
	fi
fi

sha_file=$(sha256sum "$tarFile" | awk '{print $1}')
if [ "$sha_file" != "$sha256_target" ]; then
	rm -f "$tarFile"
	abort "Checksum sumber PHP ${target} tidak cocok."
fi

mkdir -p "$backupDir" || abort "Tidak dapat membuat direktori backup."
backupFile="$backupDir/php${PHP_VER}-$(date +%Y%m%d-%H%M%S).tar.gz"

log "Mulai update PHP ${PHP_VER}: ${installed} -> ${target}"

# ------------------------------ backup ------------------------------ #
tar --exclude="${PHP_VER}/var/log/*" -czf "$backupFile" -C "$(dirname "$phpDir")" "${PHP_VER}" || abort "Backup instalasi PHP gagal."
if [ ! -s "$backupFile" ] || ! tar -tzf "$backupFile" >/dev/null 2>&1; then
	rm -f "$backupFile"
	abort "Backup instalasi PHP tidak valid, update dibatalkan."
fi
iniBackup=$(mktemp)
cp -f "$phpIni" "$iniBackup" 2>/dev/null || iniBackup=""
log "Backup dibuat: ${backupFile}"

oldModules=$(mktemp)
listPhpModules "$phpDir/bin/php" > "$oldModules"

oldSo=$(mktemp)
grep -E '^[[:space:]]*extension[[:space:]]*=' "$phpIni" 2>/dev/null | grep -oE '[A-Za-z0-9_]+\.so' | sort -u > "$oldSo"

# ------------------------------ build ------------------------------ #
rm -rf "$stageDir"
mkdir -p "$stageDir" || abort "Tidak dapat membuat direktori staging."

log "Membangun PHP ${target} di staging (PHP-FPM tetap berjalan)..."
cd "$pluginDir" || fail "Direktori plugin PHP tidak ditemukan."
PHP_UPDATE=1 PHP_INSTALL_ROOT="$stageDir" bash "$pluginDir/versions/${PHP_VER}/install.sh" install "$PHP_VER" "$target" || fail "Build PHP ${target} gagal."

stagedRoot="${stageDir}${phpDir}"
stagedPhp="${stagedRoot}/bin/php"
if [ ! -x "$stagedPhp" ]; then
	fail "Hasil build tidak ditemukan di staging."
fi

stagedVersion=$(getPhpVersion "$stagedPhp")
if [ "$stagedVersion" != "$target" ]; then
	fail "Versi hasil build (${stagedVersion:-tidak diketahui}) tidak sesuai target ${target}."
fi

# ------------------------------ swap ------------------------------ #
log "Menghentikan PHP-FPM ${PHP_VER} sebentar untuk swap..."
if command -v python3 >/dev/null 2>&1; then
	(cd "$rootPath" && python3 "$pluginDir/index.py" stop "$PHP_VER" >/dev/null 2>&1)
fi
systemctl stop php${PHP_VER} >/dev/null 2>&1

cp -a "$stagedRoot/." "$phpDir/" || fail "Menyalin hasil build ke instalasi live gagal."
echo "$target" > "$phpDir/version.pl"
if [ -n "$patchPath" ]; then
	touch "$phpDir/.php2shell_patched"
fi

extDir=$("$phpDir/bin/php-config" --extension-dir 2>/dev/null)
if [ -n "$extDir" ] && [ -s "$oldSo" ]; then
	while read -r so; do
		[ -z "$so" ] && continue
		[ -f "${extDir}/${so}" ] && continue
		log "Ekstensi ${so} tidak ditemukan, mencoba rebuild..."
		rebuildExtension "$so" || fail "Ekstensi ${so} gagal dibangun ulang."
	done < "$oldSo"
fi

# ------------------------------ start & verify ------------------------------ #
log "Menjalankan PHP-FPM ${PHP_VER}..."
if command -v python3 >/dev/null 2>&1; then
	(cd "$rootPath" && python3 "$pluginDir/index.py" start "$PHP_VER" >/dev/null 2>&1)
fi

fpmRunning=0
for i in $(seq 1 30); do
	if ps -ef | grep -v grep | grep -qE "php/${PHP_VER}/(sbin/php-fpm|etc/php-fpm.conf)"; then
		fpmRunning=1
		break
	fi
	if command -v systemctl >/dev/null 2>&1 && [ "$(systemctl is-active php${PHP_VER} 2>/dev/null)" == "active" ]; then
		fpmRunning=1
		break
	fi
	sleep 1
done

if [ "$fpmRunning" != "1" ]; then
	fail "PHP-FPM ${PHP_VER} gagal dijalankan setelah update."
fi

running=$(getPhpVersion "$phpDir/bin/php")
if [ "$running" != "$target" ]; then
	fail "PHP-FPM tidak berjalan pada versi ${target} (terdeteksi: ${running:-tidak ada})."
fi

newModules=$(mktemp)
listPhpModules "$phpDir/bin/php" > "$newModules"
missingModules=$(comm -23 "$oldModules" "$newModules")
if [ -n "$missingModules" ]; then
	log "Modul yang hilang setelah update: ${missingModules}"
	fail "Modul PHP tidak lengkap setelah update."
fi

# ------------------------------ cleanup ------------------------------ #
rm -rf "$stageDir"
rm -f "$oldModules" "$newModules" "$oldSo" "$iniBackup"
log "Update PHP ${PHP_VER} ke ${target} selesai. Backup: ${backupFile}"
