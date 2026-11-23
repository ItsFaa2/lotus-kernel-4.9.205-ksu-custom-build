#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "AK3 SAFE FLASH_BOOT - PURE BASH"
echo "============================================================"

cd "$AKHOME"

echo
echo "[1] VERIFY EXISTING SANDBOX"

test -f "$AKHOME/boot.img"
test -f "$AKHOME/Image"
test -d "$AKHOME/split_img"

echo "SANDBOX: PASS"

echo
echo "[2] CREATE CORE COPY"

cp "$CORE" "$AKHOME/ak3-safe-core.sh"

# Remove ONLY top-level setup_ak invocation.
sed -i '/^[[:space:]]*setup_ak;[[:space:]]*$/d' \
    "$AKHOME/ak3-safe-core.sh"

if grep -nE '^[[:space:]]*setup_ak;[[:space:]]*$' \
    "$AKHOME/ak3-safe-core.sh"; then
    echo "FATAL: setup_ak invocation remains"
    exit 1
fi

echo "setup_ak invocation: REMOVED"

echo
echo "[3] PATCH flash_boot WRITE SECTION"

# Replace everything from the real block write command
# until the end of the flashing error check.
#
# Start:
#   blockdev --setrw $BLOCK
#
# End:
#   fi;
#
# Immediately followed by:
#   }
#
# We use awk only as a text filter; no Python required.

awk '
BEGIN {
    patch = 0
    done = 0
}

# Start replacing at real block write.
/^[[:space:]]*blockdev --setrw \$BLOCK/ {
    print "    echo \"============================================================\";"
    print "    echo \"SAFE MODE: BLOCK WRITE SUPPRESSED\";"
    print "    echo \"SAFE MODE: boot-new.img already built\";"
    print "    echo \"SAFE MODE: no blockdev/dd/cat/nandwrite executed\";"
    print "    echo \"============================================================\";"
    print "    return 0;"
    patch = 1
    next
}

# The original flash section ends immediately before
# the closing function brace. Skip all lines while patching,
# then preserve the function closing brace.
/^[[:space:]]*}[[:space:]]*$/ {
    if (patch && !done) {
        print
        done = 1
        patch = 0
        next
    }
}

{
    if (!patch)
        print
}
' "$AKHOME/ak3-safe-core.sh" > "$AKHOME/ak3-safe-core.tmp"

mv "$AKHOME/ak3-safe-core.tmp" "$AKHOME/ak3-safe-core.sh"

echo
echo "[4] VERIFY PATCH"

grep -nE \
    'SAFE MODE|blockdev --setrw|flash_erase|nandwrite|dd if=|cat boot-new.img' \
    "$AKHOME/ak3-safe-core.sh" || true

echo
echo "[5] VERIFY DANGEROUS WRITE COMMANDS"

if grep -qE \
    '^[[:space:]]*(blockdev --setrw|flash_erase|nandwrite|dd if=|cat boot-new.img)' \
    "$AKHOME/ak3-safe-core.sh"; then

    echo "FATAL: REAL WRITE COMMAND STILL PRESENT"
    exit 1
fi

echo "REAL WRITE COMMANDS: ABSENT"

echo
echo "[6] ENVIRONMENT"

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
echo "[7] SOURCE"

source "$AKHOME/ak3-safe-core.sh"

echo "SOURCE: PASS"

echo
echo "[8] FUNCTION CHECK"

declare -F flash_boot
declare -F write_boot

echo
echo "[9] EXECUTE AK3 flash_boot"

cd "$AKHOME"

flash_boot

echo
echo "============================================================"
echo "BUILD RESULT"
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
    echo "FAIL: output > 32 MiB"
    exit 1
fi

echo
echo "[10] FINAL FORENSIC"

rm -rf "$AKHOME/final-verify"
mkdir -p "$AKHOME/final-verify"

"$BIN/magiskboot" unpack \
    -h "$AKHOME/boot-new.img"

cd "$AKHOME/final-verify"

"$BIN/magiskboot" unpack \
    -h "$AKHOME/boot-new.img" >/dev/null

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
ACTUAL=$(sha256sum kernel | awk '{print $1}')

echo
echo "FINAL KERNEL SIZE : $(stat -c '%s' kernel)"
echo "FINAL KERNEL SHA  : $ACTUAL"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "FAIL: KSU KERNEL SHA MISMATCH"
    exit 1
fi

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
