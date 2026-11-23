#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3_SRC="$ROOT/AnyKernel3"
KSU="$ROOT/build/ksu-32915384-49/arch/arm64/boot/Image"
STOCK="$ROOT/boot-lotus.img"
OUT="$ROOT/output/ak3-literal-test"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "============================================================"
echo "AK3 v0.9.2 LITERAL SANDBOX TEST"
echo "============================================================"

echo
echo "[1] PREPARE ISOLATED AK3"

cp -a "$AK3_SRC" "$OUT/AnyKernel3"

AK3="$OUT/AnyKernel3"

cp "$KSU" "$AK3/Image"

# The BLOCK is a regular file, NEVER a real partition.
# bs=1 + count=33554432 guarantees bounded I/O.
BLOCK_SPEC="$OUT/boot-ak3-output.img bs=1 count=33554432"

# Initial contents must be the stock boot image.
cp "$STOCK" "$OUT/boot-ak3-output.img"

python3 - "$AK3/anykernel.sh" "$BLOCK_SPEC" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
block = sys.argv[2]

s = p.read_text()

old = 'BLOCK=/dev/block/by-name/boot;'
new = f'BLOCK="{block}";'

if old not in s:
    raise SystemExit("ERROR: expected BLOCK declaration not found")

s = s.replace(old, new, 1)

p.write_text(s)
PY

chmod +x "$AK3/anykernel.sh"

echo
echo "[2] PRE-FLASH SANDBOX"

echo "BLOCK:"
grep '^BLOCK=' "$AK3/anykernel.sh"

echo
echo "Initial sandbox image:"
stat -c '%n %s bytes' "$OUT/boot-ak3-output.img"
sha256sum "$OUT/boot-ak3-output.img"

echo
echo "KSU payload:"
stat -c '%n %s bytes' "$AK3/Image"
sha256sum "$AK3/Image"

echo
echo "============================================================"
echo "[3] EXECUTE ACTUAL ANYKERNEL3"
echo "============================================================"

cd "$AK3"

bash ./anykernel.sh 2>&1 | tee "$OUT/ak3.log"

echo
echo "============================================================"
echo "[4] AK3 OUTPUT"
echo "============================================================"

stat -c '%n %s bytes' "$OUT/boot-ak3-output.img"
sha256sum "$OUT/boot-ak3-output.img"

echo
echo "============================================================"
echo "[5] FORENSIC OUTPUT"
echo "============================================================"

mkdir -p "$OUT/forensic"
cd "$OUT/forensic"

cp "$OUT/boot-ak3-output.img" boot.img

"$AK3/tools/magiskboot" unpack -h boot.img 2>&1 | tee header.txt

echo
echo "COMPONENTS:"

for f in kernel kernel_dtb ramdisk.cpio dtb; do
    echo
    echo "[$f]"

    if [ -f "$f" ]; then
        file "$f"
        stat -c '%n %s bytes' "$f"
        sha256sum "$f"
    else
        echo "MISSING"
    fi
done

echo
echo "============================================================"
echo "[6] AUTOMATED PAYLOAD VALIDATION"
echo "============================================================"

PASS=1

KERNEL_SHA="$(sha256sum kernel | awk '{print $1}')"
KERNEL_SIZE="$(stat -c '%s' kernel)"

RAMDISK_SHA="$(sha256sum ramdisk.cpio | awk '{print $1}')"
DTB_SHA="$(sha256sum dtb | awk '{print $1}')"
KERNEL_DTB_SHA="$(sha256sum kernel_dtb | awk '{print $1}')"
IMAGE_SIZE="$(stat -c '%s' boot.img)"

echo "IMAGE_SIZE       = $IMAGE_SIZE"
echo "KERNEL_SIZE      = $KERNEL_SIZE"
echo "KERNEL_SHA       = $KERNEL_SHA"
echo "KERNEL_DTB_SHA   = $KERNEL_DTB_SHA"
echo "RAMDISK_SHA      = $RAMDISK_SHA"
echo "DTB_SHA          = $DTB_SHA"

[ "$KERNEL_SHA" = \
"3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238" ] || {
    echo "FAIL: KERNEL SHA"
    PASS=0
}

[ "$KERNEL_SIZE" = "33943572" ] || {
    echo "FAIL: KERNEL SIZE"
    PASS=0
}

[ "$RAMDISK_SHA" = \
"1a592696fd37b76550f5e7bdedd2b74e634166064d8d6ba5fc5c28d8fb6b9d8a" ] || {
    echo "FAIL: RAMDISK SHA"
    PASS=0
}

[ "$DTB_SHA" = \
"156c9b956f25edf1e25e75454828f893b1f1d205edb25528eedeea48fb94c76a" ] || {
    echo "FAIL: DTB SHA"
    PASS=0
}

[ "$KERNEL_DTB_SHA" = \
"702f1e3839cceac8dc420c027a7a242c39a4bbe5b6f60bbd55f3e148183fc56f" ] || {
    echo "FAIL: KERNEL_DTB SHA"
    PASS=0
}

[ "$IMAGE_SIZE" -le 67108864 ] || {
    echo "FAIL: IMAGE > 64 MiB"
    PASS=0
}

grep -q 'HEADER_VER.*\[2\]' header.txt || {
    echo "FAIL: HEADER VERSION"
    PASS=0
}

grep -q 'PAGESIZE.*\[2048\]' header.txt || {
    echo "FAIL: PAGE SIZE"
    PASS=0
}

grep -q 'KERNEL_FMT.*\[gzip\]' header.txt || {
    echo "FAIL: KERNEL COMPRESSION"
    PASS=0
}

grep -q 'RAMDISK_FMT.*\[gzip\]' header.txt || {
    echo "FAIL: RAMDISK COMPRESSION"
    PASS=0
}

if [ "$PASS" -eq 1 ]; then
    echo
    echo "============================================================"
    echo "AK3 LITERAL SANDBOX TEST: PASS"
    echo "============================================================"
    echo
    echo "OUTPUT:"
    echo "$OUT/boot-ak3-output.img"
    echo
    echo "SHA256:"
    sha256sum "$OUT/boot-ak3-output.img"
else
    echo
    echo "============================================================"
    echo "AK3 LITERAL SANDBOX TEST: FAIL"
    echo "============================================================"
    exit 1
fi
