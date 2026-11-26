#!/usr/bin/env bash
# setup.sh — install everything stage 0 needs (Ubuntu / Debian / WSL).
#
#   bash setup.sh            # full install
#   SKIP_APT=1 bash setup.sh # no sudo: only venv + Ghidra + rootfs
#
# Result:
#   ~/venvs/co2full_preproc         Python 3.11 venv (override with VENV=...)
#   tools/ghidra_<ver>_PUBLIC       Ghidra (GHIDRA_HOME, picked up by config.py)
#   qiling_rootfs/x8664_linux       stock Qiling rootfs (sparse checkout)
#   qiling_rootfs/x8664_linux_glibc236
#                                   glibc 2.36 rootfs (Debian 12) — needed for
#                                   binaries that use GLIBC_2.34+ symbols
set -euo pipefail
cd "$(dirname "$0")"
HERE="$PWD"
VENV="${VENV:-$HOME/venvs/co2full_preproc}"
GHIDRA_VERSION="${GHIDRA_VERSION:-11.4.3}"
GHIDRA_DATE="${GHIDRA_DATE:-20251203}"

if [[ -z "${SKIP_APT:-}" ]]; then
    echo "[*] apt: Java 21 (Ghidra 11.2+ needs JDK 21), UPX, compilers, 7z ..."
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        openjdk-21-jdk-headless upx-ucl gcc clang python3-venv python3-pip \
        p7zip-full binutils file git unzip wget
fi

echo "[*] Python 3.11 venv at $VENV (via uv) ..."
if [[ ! -x "$VENV/bin/python" ]]; then
    python3 -m venv "$HOME/venvs/_uvboot"
    "$HOME/venvs/_uvboot/bin/pip" install -q uv
    "$HOME/venvs/_uvboot/bin/uv" venv -q --python 3.11 "$VENV"
fi
VIRTUAL_ENV="$VENV" "$HOME/venvs/_uvboot/bin/uv" pip install -q -r requirements.txt

echo "[*] Ghidra $GHIDRA_VERSION ..."
if [[ ! -d "tools/ghidra_${GHIDRA_VERSION}_PUBLIC" ]]; then
    mkdir -p tools
    wget -q "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/ghidra_${GHIDRA_VERSION}_PUBLIC_${GHIDRA_DATE}.zip" \
        -O /tmp/ghidra.zip
    unzip -q /tmp/ghidra.zip -d tools/
    rm -f /tmp/ghidra.zip
fi

echo "[*] Qiling rootfs (x86/x86_64 Linux only, sparse) ..."
if [[ ! -d qiling_rootfs/.git ]]; then
    git clone -q --depth 1 --filter=blob:none --sparse https://github.com/qilingframework/rootfs.git qiling_rootfs
    git -C qiling_rootfs sparse-checkout set x8664_linux x86_linux
fi

echo "[*] glibc 2.36 rootfs from debian:12 ..."
R="qiling_rootfs/x8664_linux_glibc236"
if [[ ! -f "$R/lib/x86_64-linux-gnu/libc.so.6" ]]; then
    DOCKER="${DOCKER:-docker}"
    if ! command -v "$DOCKER" >/dev/null && [[ -x "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" ]]; then
        DOCKER="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
    fi
    mkdir -p "$R/lib/x86_64-linux-gnu" "$R/lib64" "$R/etc" "$R/tmp"
    cid=$("$DOCKER" create debian:12-slim)
    for f in libc.so.6 libdl.so.2 libm.so.6 libpthread.so.0 libgcc_s.so.1 ld-linux-x86-64.so.2; do
        "$DOCKER" cp -L "$cid:/lib/x86_64-linux-gnu/$f" "$R/lib/x86_64-linux-gnu/$f"
    done
    "$DOCKER" rm "$cid" >/dev/null
    cp "$R/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" "$R/lib64/"
fi

cat <<EOF
[*] Done.
    source $VENV/bin/activate
    export GHIDRA_HOME=$HERE/tools/ghidra_${GHIDRA_VERSION}_PUBLIC   # optional, config.py auto-detects
    bash tests/build_samples.sh      # test binaries (needs Docker: icyguider/ollvm)
    cd tests && pytest -q
EOF
