#!/bin/bash
# Uji beban ringan memakai curl untuk plugin OpenWAF.
#
# Setiap request dikirim ke nginx lokal dengan header Host berisi domain yang
# diuji, jadi trafiknya melewati WAF yang sama seperti kunjungan sungguhan dan
# langsung terlihat di kartu real-time dashboard.
#
# Contoh:
#   ./load_test.sh rcbbcq.t.mlite.id              # 100 request, 10 paralel
#   ./load_test.sh rcbbcq.t.mlite.id 200 10       # 200 request, 10 paralel
#   ./load_test.sh basoro.loc 500 50 --stats      # tampilkan QPS WAF setelah uji
#   ./load_test.sh contoh.com 300 20 --target contoh.com --scheme https -k
#
# Lihat --help untuk daftar opsi lengkap.

set -u

DOMAIN=''
REQUESTS=100
CONCURRENCY=10
TARGET='127.0.0.1'
URL_PATH='/'
SCHEME='http'
INSECURE=0
SHOW_STATS=0

usage() {
    cat <<'EOF'
Penggunaan:
  load_test.sh <domain> [jumlah_request] [concurrency] [opsi]

Argumen:
  <domain>            Domain/situs yang diuji (dipakai sebagai header Host)
  <jumlah_request>    Jumlah request total (default 100)
  <concurrency>       Jumlah request paralel (default 10)

Opsi:
  -d, --domain <domain>       Sama dengan argumen pertama
  -n, --requests <jumlah>     Sama dengan argumen kedua
  -c, --concurrency <jumlah>  Sama dengan argumen ketiga
  -t, --target <host[:port]>  Alamat yang dihubungi (default 127.0.0.1).
                              Untuk menguji lewat DNS asli, isi nama domain.
  -u, --url <path>            Path yang diminta (default /)
  -s, --scheme <http|https>   Skema URL (default http)
  -k, --insecure              Abaikan verifikasi sertifikat TLS
      --stats                 Tampilkan statistik real-time WAF sesudah uji
  -h, --help                  Tampilkan bantuan ini

Kode keluar:
  0  semua request terjawab
  1  ada request yang gagal tersambung (HTTP 000)
  2  argumen salah
EOF
}

die() {
    echo "Error: $1" >&2
    echo "Jalankan '$(basename "$0") --help' untuk bantuan." >&2
    exit 2
}

POS=0
while [ $# -gt 0 ]; do
    case "$1" in
        -d|--domain)      [ $# -ge 2 ] || die "$1 butuh nilai";      DOMAIN="$2"; shift 2 ;;
        -n|--requests)    [ $# -ge 2 ] || die "$1 butuh nilai";      REQUESTS="$2"; shift 2 ;;
        -c|--concurrency) [ $# -ge 2 ] || die "$1 butuh nilai";      CONCURRENCY="$2"; shift 2 ;;
        -t|--target)      [ $# -ge 2 ] || die "$1 butuh nilai";      TARGET="$2"; shift 2 ;;
        -u|--url)         [ $# -ge 2 ] || die "$1 butuh nilai";      URL_PATH="$2"; shift 2 ;;
        -s|--scheme)      [ $# -ge 2 ] || die "$1 butuh nilai";      SCHEME="$2"; shift 2 ;;
        -k|--insecure)    INSECURE=1; shift ;;
        --stats)          SHOW_STATS=1; shift ;;
        -h|--help)        usage; exit 0 ;;
        -*)               die "opsi tidak dikenal: $1" ;;
        *)
            POS=$((POS + 1))
            case "$POS" in
                1) DOMAIN="$1" ;;
                2) REQUESTS="$1" ;;
                3) CONCURRENCY="$1" ;;
                *) die "argumen berlebih: $1" ;;
            esac
            shift
            ;;
    esac
done

[ -n "$DOMAIN" ] || die "domain belum diisi"
case "$REQUESTS" in
    ''|*[!0-9]*) die "jumlah request harus angka, bukan '$REQUESTS'" ;;
esac
case "$CONCURRENCY" in
    ''|*[!0-9]*) die "concurrency harus angka, bukan '$CONCURRENCY'" ;;
esac
[ "$REQUESTS" -gt 0 ] || die "jumlah request harus lebih dari 0"
[ "$CONCURRENCY" -gt 0 ] || die "concurrency harus lebih dari 0"
[ "$CONCURRENCY" -le "$REQUESTS" ] || CONCURRENCY="$REQUESTS"
case "$SCHEME" in
    http|https) ;;
    *) die "skema harus http atau https" ;;
esac

command -v curl >/dev/null 2>&1 || die "curl tidak terpasang"
command -v xargs >/dev/null 2>&1 || die "xargs tidak terpasang"

[ "${URL_PATH#/}" = "$URL_PATH" ] && URL_PATH="/$URL_PATH"
URL="${SCHEME}://${TARGET}${URL_PATH}"

CURL_ARGS=(-s -o /dev/null --max-time 30 -w '%{http_code} %{time_total}\n' -H "Host: ${DOMAIN}")
[ "$INSECURE" = 1 ] && CURL_ARGS+=(-k)

RESULT="$(mktemp)"
trap 'rm -f "$RESULT"' EXIT

echo "Uji beban WAF"
echo "  target      : ${URL} (Host: ${DOMAIN})"
echo "  request     : ${REQUESTS}, paralel: ${CONCURRENCY}"
echo "  mulai       : $(date '+%H:%M:%S')"

START="$(date +%s.%N)"
# xargs -I mengganti {} di baris perintah saja, bukan menambahkan URL di ujung.
# {} dipakai sebagai argv0 shell pembungkus (dibuang) supaya URL ikut terkirim
# dan tetap portabel di xargs GNU maupun BSD.
seq 1 "$REQUESTS" | xargs -P "$CONCURRENCY" -I{} \
    sh -c 'exec curl "$@"' sh-{} "${CURL_ARGS[@]}" "$URL" > "$RESULT"
END="$(date +%s.%N)"

TOTAL="$(wc -l < "$RESULT" | tr -d ' ')"
[ "$TOTAL" -gt 0 ] || [ "$REQUESTS" -eq 0 ] || {
    echo "Tidak ada respons tercatat." >&2
    exit 1
}

echo
echo "Hasil"
awk -v total="$TOTAL" -v start="$START" -v end="$END" -v plan="$REQUESTS" '
    { code[$1]++ }
    END {
        elapsed = end - start
        if (elapsed <= 0) elapsed = 0.001
        printf "  selesai     : %d request dalam %.2f detik (%s request/detik)\n", \
            total, elapsed, sprintf("%.1f", total / elapsed)
        if (total < plan) {
            printf "  catatan     : %d dari %d request tidak tercatat\n", plan - total, plan
        }
        printf "  status      :\n"
        for (c in code) {
            printf "STATUS %s %d %.1f\n", c, code[c], code[c] * 100 / total
        }
    }
' "$RESULT" | {
    while IFS= read -r line; do
        case "$line" in
            "STATUS "*)
                # status code, jumlah, persen
                set -- $line
                printf "      HTTP %-4s %6d  (%.1f%%)\n" "$2" "$3" "$4"
                ;;
            *) echo "$line" ;;
        esac
    done
}

# Sebaran waktu respons (sudut pandang klien, termasuk koneksi)
awk '{print $2}' "$RESULT" | sort -n | awk '
    { t[NR] = $1 + 0 }
    END {
        n = NR
        if (n == 0) exit
        sum = 0
        for (i = 1; i <= n; i++) sum += t[i]
        p50 = int((n + 1) * 0.50); if (p50 < 1) p50 = 1; if (p50 > n) p50 = n
        p95 = int((n + 1) * 0.95); if (p95 < 1) p95 = 1; if (p95 > n) p95 = n
        printf "  waktu       : rata-rata %.3fs, p50 %.3fs, p95 %.3f , maks %.3f , min %.3fs\n", \
            sum / n, t[p50], t[p95], t[n], t[1]
    }
'

if grep -q '^000 ' "$RESULT"; then
    echo
    echo "Ada request yang gagal tersambung (000). Periksa target, port, dan skema." >&2
    GREP_FAIL=1
else
    GREP_FAIL=0
fi

if [ "$SHOW_STATS" = 1 ]; then
    PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
    PYTHON="${PLUGIN_DIR}/../../bin/python3"
    # Bucket hanya terlihat setelah timer nginx menulis realtime.json
    echo
    echo "Menunggu timer WAF menulis statistik..."
    sleep 6
    echo
    echo "Statistik real-time WAF"
    if [ -x "$PYTHON" ]; then
        "$PYTHON" "${PLUGIN_DIR}/index.py" get_realtime_stats '' '{}'
    else
        echo "  python panel tidak ditemukan di ${PYTHON}"
        echo "  jalankan manual: cd ${PLUGIN_DIR} && python3 index.py get_realtime_stats '' '{}'"
    fi
fi

[ "$GREP_FAIL" = 0 ]
