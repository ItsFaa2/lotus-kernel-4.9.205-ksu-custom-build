#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
BIN="$AK3/tools"
AKHOME="$ROOT/output/ak3-literal-test/work"

echo "============================================================"
echo "AK3 FLASH_BOOT FORENSIC - SAFE BUILD ONLY"
echo "============================================================"

rm -rf "$AKHOME"
mkdir -p "$AKHOME/split_img"

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
echo "[4] INSTALL KSU KERNEL"

cp \
    "$ROOT/build/ksu-32915384-49/arch/arm64/boot/Image" \
    "$AKHOME/Image"

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
ACTUAL=$(sha256sum "$AKHOME/Image" | awk '{print $1}')

stat -c '%s bytes' "$AKHOME/Image"
echo "$ACTUAL  Image"

[ "$ACTUAL" = "$EXPECTED" ] || {
    echo "FATAL: KSU IMAGE SHA MISMATCH"
    exit 1
}

echo "KSU IMAGE: PASS"

echo
echo "[5] BUILD AK3 split_img SANDBOX"

# AK3 flash_boot() expects these inside $SPLITIMG.
cp "$AKHOME/ramdisk.cpio" \
   "$AKHOME/split_img/ramdisk.cpio"

cp "$AKHOME/kernel_dtb" \
   "$AKHOME/split_img/kernel_dtb"

cp "$AKHOME/dtb" \
   "$AKHOME/split_img/dtb"

echo
echo "SPLIT TREE:"
find "$AKHOME/split_img" -maxdepth 1 -type f -printf '%f %s bytes\n' | sort

echo
echo "[6] AK3 ENVIRONMENT"

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
echo "[7] CREATE AK3 CORE WITHOUT setup_ak"

awk '
    /^[[:space:]]*setup_ak;[[:space:]]*$/ {
        next
    }
    { print }
' "$CORE" > "$AKHOME/ak3-core-nosetup.sh"

if grep -nE '^[[:space:]]*setup_ak;[[:space:]]*$' \
    "$AKHOME/ak3-core-nosetup.sh"; then
    echo "FATAL: setup_ak invocation remains"
    exit 1
fi

echo "setup_ak invocation: REMOVED"

echo
echo "[8] SOURCE AK3 CORE"

source "$AKHOME/ak3-core-nosetup.sh"

echo "SOURCE: PASS"

echo
echo "[9] NORMALIZE AK3 VARIABLES"

# Source initializes these relative to AKHOME.
# Reassert BIN because this test intentionally uses the original AK3 tools.
BIN="$AK3/tools"
BOOTIMG="$AKHOME/boot.img"
SPLITIMG="$AKHOME/split_img"

export BIN BOOTIMG SPLITIMG

echo "BIN    : $BIN"
echo "BOOTIMG: $BOOTIMG"
echo "SPLIT  : $SPLITIMG"

echo
echo "[10] CREATE SAFE flash_boot()"

# Extract original flash_boot() body and replace ONLY the
# real block-device write section.
#
# Original:
#
#   blockdev --setrw $BLOCK
#   ...
#   dd/cat -> $BLOCK
#
# becomes:
#
#   echo SAFE...
#   return 0
#
# Everything before that remains original AK3 logic.

python3 - "$AKHOME/ak3-core-nosetup.sh" "$AKHOME/ak3-safe-flashboot.sh" <<'PY'
import sys

src = open(sys.argv[1], "r", encoding="utf-8").read()
out = sys.argv[2]

start = src.index("flash_boot() {")
end = src.index("\n}\n\n# flash_generic", start) + 3

func = src[start:end]

write_start = func.index("    blockdev --setrw $BLOCK")
write_end = func.index(
    "    if [ $? != 0 ]; then\n"
    "      abort \"Flashing image failed. Aborting...\";\n"
    "    fi;",
    write_start
)

write_end += len(
    "    if [ $? != 0 ]; then\n"
    "      abort \"Flashing image failed. Aborting...\";\n"
    "    fi;"
)

safe = (
    func[:write_start]
    + '    echo "SAFE MODE: BLOCK WRITE SUPPRESSED";\n'
    + '    return 0;\n'
    + func[write_end:]
)

with open(out, "w", encoding="utf-8") as f:
    f.write(safe + "\n")

print("Original flash_boot() extracted.")
print("Real block write section replaced with return 0.")
PY

echo
echo "[11] LOAD SAFE flash_boot"

source "$AKHOME/ak3-safe-flashboot.sh"

declare -F flash_boot

echo
echo "[12] RUN AK3 BUILD PATH"

flash_boot

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT RESULT"
echo "============================================================"

if [ ! -f "$AKHOME/boot-new.img" ]; then
    echo "FAIL: boot-new.img NOT CREATED"
    exit 1
fi

SIZE=$(stat -c '%s' "$AKHOME/boot-new.img")
SHA=$(sha256sum "$AKHOME/boot-new.img" | awk '{print $1}')

echo "SIZE : $SIZE bytes"
echo "SHA  : $SHA"

echo
echo "[13] VERIFY OUTPUT"

if [ "$SIZE" -gt 33554432 ]; then
    echo "FAIL: output exceeds stock boot size"
    exit 1
fi

echo
echo "[14] MAGISKBOOT FORENSIC"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img"

echo
echo "[15] VERIFY KSU PAYLOAD"

rm -rf "$AKHOME/verify"
mkdir -p "$AKHOME/verify"

cd "$AKHOME/verify"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img" >/dev/null

KERNEL_SHA=$(sha256sum kernel | awk '{print $1}')
KERNEL_SIZE=$(stat -c '%s' kernel)

echo "KERNEL SIZE : $KERNEL_SIZE"
echo "KERNEL SHA  : $KERNEL_SHA"

[ "$KERNEL_SHA" = "$EXPECTED" ] || {
    echo "FAIL: final kernel SHA mismatch"
    exit 1
}

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
