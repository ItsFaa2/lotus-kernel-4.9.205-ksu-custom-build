#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
BIN="$AK3/tools"
AKHOME="$ROOT/output/ak3-literal-test/work"

echo "============================================================"
echo "AK3 FLASH_BOOT FORENSIC - NO SETUP_AK"
echo "============================================================"

rm -rf "$AKHOME"
mkdir -p "$AKHOME"

cd "$AKHOME"

echo
echo "[1] STOCK BOOT"

cp "$ROOT/boot-lotus.img" boot.img
sha256sum boot.img

echo
echo "[2] UNPACK STOCK"

"$BIN/magiskboot" unpack -h boot.img 2>&1 | tee unpack.log

echo
echo "[3] STOCK COMPONENTS"

for f in kernel kernel_dtb ramdisk.cpio dtb; do
    if [ -f "$f" ]; then
        printf "%-14s " "$f"
        stat -c '%s bytes' "$f"
        sha256sum "$f"
    else
        echo "$f : MISSING"
    fi
done

echo
echo "[4] REPLACE KERNEL WITH KSU"

cp \
    "$ROOT/build/ksu-32915384-49/arch/arm64/boot/Image" \
    kernel

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
ACTUAL=$(sha256sum kernel | awk '{print $1}')

stat -c '%s bytes' kernel
echo "$ACTUAL  kernel"

[ "$ACTUAL" = "$EXPECTED" ] || {
    echo "FATAL: KSU KERNEL SHA MISMATCH"
    exit 1
}

echo "KSU KERNEL: PASS"

echo
echo "[5] PREPARE AK3 ENVIRONMENT"

export AKHOME
export BIN
export BOOTIMG="$AKHOME/boot.img"
export PATCH="$AKHOME/patch"
export RAMDISK="$AKHOME/ramdisk"
export SPLITIMG="$AKHOME/split_img"
export VENDORRD="$AKHOME/vendor_ramdisk"

export OUTFD=1
export RAMDISK_COMPRESSION=auto
export PATCH_VBMETA_FLAG=auto

export PATH="$BIN:$PATH"

echo "AKHOME : $AKHOME"
echo "BIN    : $BIN"
echo "BOOTIMG: $BOOTIMG"

echo
echo "[6] CREATE CORE WITHOUT setup_ak INVOCATION"

# Remove ONLY the final top-level invocation:
#     setup_ak;
#
# Function definition:
#     setup_ak() {
# is preserved.
#
awk '
    BEGIN { removed=0 }
    /^[[:space:]]*setup_ak;[[:space:]]*$/ {
        removed=1
        next
    }
    { print }
    END {
        if (!removed) {
            print "FATAL: setup_ak; invocation not found" > "/dev/stderr"
            exit 1
        }
    }
' "$CORE" > "$AKHOME/ak3-core-nosetup.sh"

echo "Checking filtered core..."

if grep -nE '^[[:space:]]*setup_ak;[[:space:]]*$' \
    "$AKHOME/ak3-core-nosetup.sh"; then
    echo "FATAL: setup_ak invocation still present"
    exit 1
fi

if ! grep -nE '^setup_ak\(\)[[:space:]]*\{' "$AKHOME/ak3-core-nosetup.sh"; then
    echo "FATAL: setup_ak function definition missing"
    exit 1
fi

echo "setup_ak(): definition preserved"
echo "setup_ak; invocation removed"

echo
echo "[7] SOURCE"

source "$AKHOME/ak3-core-nosetup.sh"

echo "SOURCE: PASS"

echo
echo "[8] FUNCTION CHECK"

declare -F split_boot
declare -F unpack_ramdisk
declare -F repack_ramdisk
declare -F flash_boot
declare -F write_boot

echo
echo "[9] RUN ORIGINAL AK3 flash_boot()"

flash_boot

echo
echo "============================================================"
echo "AK3 FLASH_BOOT RESULT"
echo "============================================================"

if [ ! -f "$AKHOME/boot-new.img" ]; then
    echo "FAIL: boot-new.img missing"
    exit 1
fi

SIZE=$(stat -c '%s' "$AKHOME/boot-new.img")
SHA=$(sha256sum "$AKHOME/boot-new.img" | awk '{print $1}')

echo "SIZE : $SIZE bytes"
echo "SHA  : $SHA"

if [ "$SIZE" -gt 33554432 ]; then
    echo "FAIL: output exceeds stock 32 MiB"
    exit 1
fi

echo
echo "AK3 FLASH_BOOT: PASS"
