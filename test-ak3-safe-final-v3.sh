#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "AK3 SAFE FLASH_BOOT V3 - EXACT SOURCE PATCH"
echo "============================================================"

cd "$AKHOME"

echo
echo "[1] VERIFY SOURCE"

test -f "$CORE"
test -f "$AKHOME/boot.img"
test -f "$AKHOME/Image"
test -d "$AKHOME/split_img"

echo "SOURCE/SANDBOX: PASS"

echo
echo "[2] CREATE CORE COPY"

cp "$CORE" "$AKHOME/ak3-safe-core.sh"

sed -i '/^[[:space:]]*setup_ak;[[:space:]]*$/d' \
    "$AKHOME/ak3-safe-core.sh"

echo "setup_ak invocation: REMOVED"

echo
echo "[3] LOCATE flash_boot WRITE SECTION"

START=$(grep -n '^flash_boot() {' "$AKHOME/ak3-safe-core.sh" | cut -d: -f1)

if [ -z "$START" ]; then
    echo "FATAL: flash_boot() not found"
    exit 1
fi

WRITE=$(grep -n '^[[:space:]]*blockdev --setrw \$BLOCK' \
    "$AKHOME/ak3-safe-core.sh" | head -1 | cut -d: -f1)

if [ -z "$WRITE" ]; then
    echo "FATAL: flash_boot block write not found"
    exit 1
fi

echo "flash_boot START : $START"
echo "WRITE START      : $WRITE"

echo
echo "[4] SHOW ORIGINAL WRITE TAIL"

sed -n "$((WRITE-3)),$((WRITE+16))p" \
    "$AKHOME/ak3-safe-core.sh"

echo
echo "[5] EXACT PATCH"

# Build a new file:
#
#   original before blockdev
#   SAFE MODE
#   original final function brace
#
# We identify the function closing brace by scanning forward
# from the write section and counting braces.

awk -v start="$WRITE" '
NR < start {
    print
    next
}

NR == start {
    print "    echo \"============================================================\";"
    print "    echo \"SAFE MODE: BLOCK WRITE SUPPRESSED\";"
    print "    echo \"SAFE MODE: boot-new.img already built\";"
    print "    echo \"SAFE MODE: no blockdev/dd/cat/nandwrite executed\";"
    print "    echo \"============================================================\";"
    print "    return 0;"

    skip = 1
    next
}

skip {
    # The write section is always immediately before the
    # flash_boot() closing brace.
    #
    # Find the next line that is exactly two-space-indented
    # closing brace.
    if ($0 ~ /^  \}$/) {
        print
        skip = 0
        done = 1
    }

    next
}

{
    print
}
' "$AKHOME/ak3-safe-core.sh" > "$AKHOME/ak3-safe-core.tmp"

mv "$AKHOME/ak3-safe-core.tmp" "$AKHOME/ak3-safe-core.sh"

echo "PATCH: DONE"

echo
echo "[6] VERIFY FLASH_BOOT STRUCTURE"

sed -n "$START,$((START+220))p" \
    "$AKHOME/ak3-safe-core.sh" |
    tail -80

echo
echo "[7] SYNTAX CHECK"

bash -n "$AKHOME/ak3-safe-core.sh"

echo "SYNTAX: PASS"

echo
echo "[8] VERIFY SAFE PATCH"

FLASH_START=$(grep -n '^flash_boot() {' \
    "$AKHOME/ak3-safe-core.sh" |
    cut -d: -f1)

FLASH_END=$(awk -v s="$FLASH_START" '
NR > s && /^  \}$/ {
    print NR
    exit
}' "$AKHOME/ak3-safe-core.sh")

echo "FLASH_BOOT RANGE: $FLASH_START-$FLASH_END"

FLASH_BODY=$(sed -n "$FLASH_START,$FLASH_END p" \
    "$AKHOME/ak3-safe-core.sh")

if printf '%s\n' "$FLASH_BODY" |
    grep -qE '^[[:space:]]*blockdev --setrw \$BLOCK'; then
    echo "FATAL: blockdev write remains"
    exit 1
fi

if printf '%s\n' "$FLASH_BODY" |
    grep -qE '^[[:space:]]*(flash_erase|nandwrite|dd if=|cat boot-new\.img)'; then
    echo "FATAL: flash write remains"
    exit 1
fi

if ! printf '%s\n' "$FLASH_BODY" |
    grep -q 'SAFE MODE: BLOCK WRITE SUPPRESSED'; then
    echo "FATAL: SAFE MODE missing"
    exit 1
fi

echo "FLASH_BOOT WRITE: SAFE"

echo
echo "[9] ENVIRONMENT"

export AKHOME
export BIN="$AK3/tools"
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

echo "AKHOME : $AKHOME"
echo "BIN    : $BIN"
echo "BOOTIMG: $BOOTIMG"
echo "SPLIT  : $SPLITIMG"

echo
echo "[10] SOURCE"

source "$AKHOME/ak3-safe-core.sh"

echo "SOURCE: PASS"

echo
echo "[11] RUN flash_boot"

cd "$AKHOME"

flash_boot

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT RESULT"
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
    echo "FAIL: boot-new.img > stock 32 MiB"
    exit 1
fi

echo
echo "[12] FINAL FORENSIC"

rm -rf "$AKHOME/final-verify"
mkdir -p "$AKHOME/final-verify"

cd "$AKHOME/final-verify"

"$BIN/magiskboot" unpack -h \
    "$AKHOME/boot-new.img"

echo
echo "[13] VERIFY KSU KERNEL"

ACTUAL=$(sha256sum kernel | awk '{print $1}')
SIZE=$(stat -c '%s' kernel)

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"

echo "KERNEL SIZE : $SIZE"
echo "KERNEL SHA  : $ACTUAL"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "FAIL: KSU kernel SHA mismatch"
    exit 1
fi

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
