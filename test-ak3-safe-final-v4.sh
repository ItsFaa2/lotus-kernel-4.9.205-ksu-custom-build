#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "AK3 SAFE FLASH_BOOT V4 - EXACT LINE REPLACEMENT"
echo "============================================================"

cd "$AKHOME"

echo
echo "[1] VERIFY SANDBOX"

test -f "$CORE"
test -f "$AKHOME/boot.img"
test -f "$AKHOME/Image"
test -d "$AKHOME/split_img"

echo "SANDBOX: PASS"

echo
echo "[2] FRESH CORE COPY"

cp "$CORE" "$AKHOME/ak3-safe-core.sh"

sed -i '/^[[:space:]]*setup_ak;[[:space:]]*$/d' \
    "$AKHOME/ak3-safe-core.sh"

echo "setup_ak invocation: REMOVED"

echo
echo "[3] VERIFY ORIGINAL WRITE RANGE"

sed -n '510,532p' "$AKHOME/ak3-safe-core.sh"

echo
echo "[4] PATCH EXACT LINES 516-528"

sed -i '516,528c\
    echo "============================================================";\
    echo "SAFE MODE: BLOCK WRITE SUPPRESSED";\
    echo "SAFE MODE: boot-new.img already built";\
    echo "SAFE MODE: no blockdev/dd/cat/nandwrite executed";\
    echo "============================================================";\
    return 0;
' "$AKHOME/ak3-safe-core.sh"

echo "EXACT PATCH: DONE"

echo
echo "[5] VERIFY PATCHED RANGE"

sed -n '510,532p' "$AKHOME/ak3-safe-core.sh"

echo
echo "[6] SYNTAX CHECK"

bash -n "$AKHOME/ak3-safe-core.sh"

echo "SYNTAX: PASS"

echo
echo "[7] VERIFY flash_boot() ONLY"

FLASH_START=$(grep -n '^flash_boot() {' \
    "$AKHOME/ak3-safe-core.sh" |
    cut -d: -f1)

FLASH_END=$(awk -v start="$FLASH_START" '
NR > start && $0 == "}" {
    print NR
    exit
}' "$AKHOME/ak3-safe-core.sh")

echo "flash_boot START : $FLASH_START"
echo "flash_boot END   : $FLASH_END"

if [ -z "$FLASH_END" ]; then
    echo "FATAL: flash_boot closing brace not found"
    exit 1
fi

FLASH_BODY=$(sed -n "${FLASH_START},${FLASH_END}p" \
    "$AKHOME/ak3-safe-core.sh")

if printf '%s\n' "$FLASH_BODY" |
    grep -qE '^[[:space:]]*blockdev --setrw \$BLOCK'; then
    echo "FATAL: blockdev remains inside flash_boot"
    exit 1
fi

if printf '%s\n' "$FLASH_BODY" |
    grep -qE '^[[:space:]]*(flash_erase|nandwrite|dd if=|cat boot-new\.img)'; then
    echo "FATAL: write command remains inside flash_boot"
    exit 1
fi

if ! printf '%s\n' "$FLASH_BODY" |
    grep -q 'SAFE MODE: BLOCK WRITE SUPPRESSED'; then
    echo "FATAL: SAFE MODE missing"
    exit 1
fi

echo "flash_boot(): SAFE"

echo
echo "[8] ENVIRONMENT"

export AKHOME="$AKHOME"
export BIN="$BIN"
export BOOTIMG="$AKHOME/boot.img"
export PATCH="$AKHOME/patch"
export RAMDISK="$AKHOME/ramdisk"
export SPLITIMG="$AKHOME/split_img"
export VENDORRD="$AKHOME/vendor_ramdisk"

export OUTFD=1
export RAMDISK_COMPRESSION=auto
export PATCH_VBMETA_FLAG=auto
export NO_MAGISK_CHECK=1
export PATH="$BIN:$PATH"

# Explicitly non-device path.
export BLOCK="$AKHOME/SAFE_BLOCK_DO_NOT_FLASH"

echo "AKHOME : $AKHOME"
echo "BIN    : $BIN"
echo "BOOTIMG: $BOOTIMG"
echo "SPLIT  : $SPLITIMG"
echo "BLOCK  : $BLOCK"

case "$BLOCK" in
    /dev/*)
        echo "FATAL: BLOCK points to /dev"
        exit 1
        ;;
esac

echo
echo "[9] SOURCE CORE"

source "$AKHOME/ak3-safe-core.sh"

# ak3-core.sh initializes BIN/paths itself.
# Reassert our sandbox tool path after sourcing.
export BIN="$AK3/tools"
export PATH="$BIN:$PATH"

echo "SOURCE: PASS"

echo
echo "[10] RUN flash_boot()"

cd "$AKHOME"

flash_boot

echo
echo "[11] VERIFY boot-new.img"

if [ ! -f "$AKHOME/boot-new.img" ]; then
    echo "FAIL: boot-new.img missing"
    exit 1
fi

SIZE=$(stat -c '%s' "$AKHOME/boot-new.img")
SHA=$(sha256sum "$AKHOME/boot-new.img" | awk '{print $1}')

echo "SIZE : $SIZE"
echo "SHA  : $SHA"

if [ "$SIZE" -gt "$(stat -c '%s' "$AKHOME/boot.img")" ]; then
    echo "FAIL: output larger than stock boot.img"
    exit 1
fi

echo
echo "[12] FORENSIC UNPACK"

rm -rf "$AKHOME/final-verify"
mkdir -p "$AKHOME/final-verify"

cd "$AKHOME/final-verify"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img"

echo
echo "[13] VERIFY KSU KERNEL"

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"

if [ ! -f kernel ]; then
    echo "FAIL: unpacked kernel missing"
    exit 1
fi

KERNEL_SIZE=$(stat -c '%s' kernel)
KERNEL_SHA=$(sha256sum kernel | awk '{print $1}')

echo "KERNEL SIZE : $KERNEL_SIZE"
echo "KERNEL SHA  : $KERNEL_SHA"

if [ "$KERNEL_SHA" != "$EXPECTED" ]; then
    echo "FAIL: KSU kernel SHA mismatch"
    exit 1
fi

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT V4: PASS"
echo "============================================================"
echo "KSU kernel preserved"
echo "boot-new.img generated"
echo "NO REAL BLOCK DEVICE WRITTEN"
