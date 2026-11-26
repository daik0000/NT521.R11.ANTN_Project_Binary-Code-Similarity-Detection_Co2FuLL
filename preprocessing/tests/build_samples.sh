#!/usr/bin/env bash
# Build the test binaries described in section 8.1 of the design doc.
#
# Compilation happens inside the `icyguider/ollvm` Docker image
# (heroims/obfuscator, LLVM 13 + Debian 12 gcc/mingw). UPX packing is done
# with the host `upx`.
#
# Works on plain Linux (native docker) and on WSL with Docker Desktop's
# Windows docker.exe (paths are converted with wslpath -w).
#
# Usage:  bash tests/build_samples.sh            # build into tests/bin/
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/samples"
OUT="$HERE/bin"
IMAGE="${OLLVM_IMAGE:-icyguider/ollvm}"
mkdir -p "$OUT"

# ---- locate docker ---------------------------------------------------------
DOCKER="${DOCKER:-}"
if [[ -z "$DOCKER" ]]; then
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        DOCKER=docker
    elif [[ -x "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" ]]; then
        DOCKER="/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
    else
        echo "[!] docker not found (set DOCKER=/path/to/docker)" >&2
        exit 1
    fi
fi
host_path() {  # path as seen by the docker daemon
    if [[ "$DOCKER" == *.exe ]]; then wslpath -w "$1"; else echo "$1"; fi
}

run_in_image() {
    "$DOCKER" run --rm -v "$(host_path "$SRC"):/src:ro" -v "$(host_path "$OUT"):/out" \
        --entrypoint bash "$IMAGE" -c "$1"
}

echo "[*] Compiling samples in $IMAGE ..."
run_in_image '
set -e
cd /src
OBF="-mllvm -fla -mllvm -bcf -mllvm -sub"
# 1. clean (design: gcc -O2) + same-compiler baseline for structural diffs
gcc   -O2 -o /out/test_clean      test_subject.c
clang -O0 -o /out/test_clean_O0   test_subject.c
# 2. OLLVM: control-flow flattening + bogus control flow + substitution
clang -O0 $OBF -o /out/test_ollvm      test_subject.c
# 2b. OLLVM + string obfuscation (Nhom 2 strings)
clang -O0 $OBF -mllvm -sobf -o /out/test_ollvm_sobf test_subject.c
# 4. import hiding + XOR strings (Nhom 2 imports)
clang -O0 -o /out/test_hidden test_hidden.c -ldl
# 5. Windows PE variants (detection on PE)
x86_64-w64-mingw32-gcc -O2 -o /out/test_clean.exe test_subject.c
x86_64-w64-mingw32-clang -O0 $OBF -o /out/test_ollvm.exe test_subject.c 2>/dev/null \
    || echo "[warn] mingw clang OLLVM build failed (optional)"
chmod 755 /out/* || true
'

# ---- 3. UPX packing ----------------------------------------------------------
if command -v upx >/dev/null 2>&1; then
    echo "[*] Packing with UPX ..."
    for b in test_ollvm test_clean test_hidden; do
        rm -f "$OUT/${b}_upx"
        # small ELFs can be rejected by UPX; --force-pie keeps PIE binaries packable
        upx -q --best -o "$OUT/${b}_upx" "$OUT/$b" >/dev/null 2>&1 \
            || upx -q --best --force -o "$OUT/${b}_upx" "$OUT/$b" >/dev/null \
            || echo "[warn] UPX failed for $b"
    done
else
    echo "[warn] upx not installed — packed samples skipped"
fi

ls -l "$OUT"
