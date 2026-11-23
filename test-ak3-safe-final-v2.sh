#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "AK3 SAFE FLASH_BOOT - SCOPED WRITE CHECK"
echo "============================================================"

cd "$AKHOME"

test -f "$AKHOME/boot.img"
test -f "$AKHOME/Image"
test -d "$AKHOME/split_img"

echo
echo "[1] CREATE CORE COPY"

cp "$CORE" "$AKHOME/ak3-safe-core.sh"

sed -i '/^[[:space:]]*setup_ak;[[:space:]]*$/d' \
    "$AKHOME/ak3-safe-core.sh"

if grep -qE '^[[:space:]]*setup_ak;[[:space:]]*$' \
    "$AKHOME/ak3-safe-core.sh"; then
    echo "FATAL: setup_ak invocation remains"
    exit 1
fi

echo "setup_ak invocation: REMOVED"

echo
echo "[2] PATCH ONLY flash_boot() WRITE"

awk '
BEGIN {
    in_flash = 0
    patched = 0
}

# Enter flash_boot.
/^flash_boot\(\)[[:space:]]*\{/ {
    in_flash = 1
    print
    next
}

# Inside flash_boot, replace the first real block write.
/^[[:space:]]*blockdev --setrw \$BLOCK/ {
    if (in_flash && !patched) {
        print "    echo \"============================================================\";"
        print "    echo \"SAFE MODE: BLOCK WRITE SUPPRESSED\";"
        print "    echo \"SAFE MODE: boot-new.img already built\";"
        print "    echo \"SAFE MODE: no blockdev/dd/cat/nandwrite executed\";"
        print "    echo \"============================================================\";"
        print "    return 0;"
        patched = 1
        next
    }
}

# Once inside flash_boot, skip original write commands.
# Stop skipping at its closing brace.
{
    if (in_flash && patched) {
        if ($0 ~ /^[[:space:]]*blockdev --setrw \$BLOCK/) next
        if ($0 ~ /^[[:space:]]*(flash_erase|nandwrite)/) next
        if ($0 ~ /^[[:space:]]*dd if=/) next
        if ($0 ~ /^[[:space:]]*cat boot-new\.img/) next
    }

    print

    # flash_boot ends at this closing brace after it was patched.
    if (in_flash && patched && $0 ~ /^  \}$/) {
        in_flash = 0
    }
}

END {
    if (!patched) {
        print "FATAL: flash_boot write section was not patched" > "/dev/stderr"
        exit 1
    }
}
' "$AKHOME/ak3-safe-core.sh" > "$AKHOME/ak3-safe-core.tmp"

mv "$AKHOME/ak3-safe-core.tmp" "$AKHOME/ak3-safe-core.sh"

echo "flash_boot write section: PATCHED"

echo
echo "[3] VERIFY flash_boot() ONLY"

sed -n '312,530p' "$AKHOME/ak3-safe-core.sh" |
    grep -nE \
    'blockdev --setrw \$BLOCK|flash_erase|nandwrite|dd if=|cat boot-new\.img|SAFE MODE|return 0'

echo
echo "[4] VERIFY SAFE PATCH"

FLASH_BLOCK=$(sed -n '312,530p' "$AKHOME/ak3-safe-core.sh")

if printf '%s\n' "$FLASH_BLOCK" |
    grep -qE '^[[:space:]]*blockdev --setrw \$BLOCK'; then
    echo "FATAL: flash_boot still contains blockdev --setrw"
    exit 1
fi

if printf '%s\n' "$FLASH_BLOCK" |
    grep -qE '^[[:space:]]*(flash_erase|nandwrite|dd if=|cat boot-new\.img)'; then
    echo "FATAL: flash_boot still contains write operation"
    exit 1
fi

if ! printf '%s\n' "$FLASH_BLOCK" |
    grep -q 'SAFE MODE: BLOCK WRITE SUPPRESSED'; then
    echo "FATAL: SAFE MODE marker missing"
    exit 1
fi

echo "flash_boot(): SAFE"

echo
echo "[5] ENVIRONMENT"

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
echo "[6] SOURCE"

source "$AKHOME/ak3-safe-core.sh"

echo "SOURCE: PASS"

echo
echo "[7] FUNCTION CHECK"

declare -F flash_boot
declare -F write_boot

echo
echo "[8] RUN flash_boot()"

cd "$AKHOME"

flash_boot

echo
echo "============================================================"
echo "BUILD RESULT"
echo "============================================================"

test -f "$AKHOME/boot-new.img" || {
    echo "FAIL: boot-new.img missing"
    exit 1
}

SIZE=$(stat -c '%s' "$AKHOME/boot-new.img")
SHA=$(sha256sum "$AKHOME/boot-new.img" | awk '{print $1}')

echo "SIZE : $SIZE bytes"
echo "SHA  : $SHA"

if [ "$SIZE" -gt 33554432 ]; then
    echo "FAIL: output exceeds stock boot size"
    exit 1
fi

echo
echo "[9] FINAL FORENSIC"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img"

echo
echo "[10] VERIFY FINAL KSU KERNEL"

rm -rf "$AKHOME/final-verify"
mkdir -p "$AKHOME/final-verify"

"$BIN/magiskboot" unpack \
    -h "$AKHOME/boot-new.img" \
    "$AKHOME/final-verify" >/dev/null 2>&1 || true

# magiskboot uses current directory for unpack.
cd "$AKHOME/final-verify"

"$BIN/magiskboot" unpack \
    -h "$AKHOME/boot-new.img" >/dev/null

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
ACTUAL=$(sha256sum kernel | awk '{print $1}')

echo "KERNEL SIZE : $(stat -c '%s' kernel)"
echo "KERNEL SHA  : $ACTUAL"

[ "$ACTUAL" = "$EXPECTED" ] || {
    echo "FAIL: final KSU kernel SHA mismatch"
    exit 1
}

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
