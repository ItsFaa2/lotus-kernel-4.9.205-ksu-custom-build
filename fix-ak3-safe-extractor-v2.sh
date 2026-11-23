#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "AK3 SAFE FLASH_BOOT EXTRACTOR V2"
echo "============================================================"

cd "$AKHOME"

echo
echo "[1] SOURCE RANGE"

sed -n '313,529p' "$CORE" > "$AKHOME/ak3-flashboot-original.sh"

wc -l "$AKHOME/ak3-flashboot-original.sh"

echo
echo "[2] PATCH REAL WRITE SECTION"

python3 - "$AKHOME/ak3-flashboot-original.sh" "$AKHOME/ak3-safe-flashboot.sh" <<'PY'
import sys

src_path = sys.argv[1]
out_path = sys.argv[2]

lines = open(src_path, encoding="utf-8").readlines()

# Original source lines 313..529 inclusive.
# Local indices:
#   source 313 -> index 0
#   source 516 -> index 203
#   source 528 -> index 215
#   source 529 -> index 216

if len(lines) != 217:
    print(f"FATAL: expected 217 lines, got {len(lines)}")
    sys.exit(1)

print("EXTRACTED LINES:", len(lines))

# Verify anchors before modifying.
assert lines[0].startswith("flash_boot() {"), repr(lines[0])
assert "blockdev --setrw $BLOCK" in lines[203], repr(lines[203])
assert "Flashing image failed. Aborting..." in lines[215], repr(lines[215])
assert lines[216].strip() == "}", repr(lines[216])

print("ANCHORS: PASS")

# Keep source through line 515.
# Replace original lines 516..528.
# Keep closing function brace line 529.
safe = lines[:203] + [
    '    echo "============================================================";\n',
    '    echo "SAFE MODE: BLOCK WRITE SUPPRESSED";\n',
    '    echo "SAFE MODE: boot-new.img built successfully";\n',
    '    echo "SAFE MODE: no blockdev/dd/cat/nandwrite executed";\n',
    '    echo "============================================================";\n',
    '    return 0;\n',
] + [lines[216]]

with open(out_path, "w", encoding="utf-8") as f:
    f.writelines(safe)

print("SAFE FUNCTION: CREATED")
print("SAFE FUNCTION LINES:", len(safe))
PY

echo
echo "[3] VERIFY SAFE FUNCTION"

nl -ba "$AKHOME/ak3-safe-flashboot.sh" | tail -30

echo
echo "[4] VERIFY DANGEROUS WRITE CALLS ABSENT"

if grep -nE \
    'blockdev --setrw|flash_erase|nandwrite|dd if=|cat boot-new.img' \
    "$AKHOME/ak3-safe-flashboot.sh"; then

    echo "FATAL: dangerous write operation still exists"
    exit 1
fi

echo "WRITE OPERATIONS: ABSENT"

echo
echo "[5] SOURCE SAFE FUNCTION"

export AKHOME
export BIN="$AK3/tools"
export BOOTIMG="$AKHOME/boot.img"
export SPLITIMG="$AKHOME/split_img"
export RAMDISK_COMPRESSION=auto
export PATCH_VBMETA_FLAG=auto
export NO_MAGISK_CHECK=1
export OUTFD=1
export PATH="$BIN:$PATH"

source "$AKHOME/ak3-safe-flashboot.sh"

declare -F flash_boot

echo
echo "[6] EXECUTE AK3 BUILD"

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

echo
echo "[7] FINAL FORENSIC"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img"

echo
echo "[8] EXTRACT FINAL KERNEL"

VERIFY="$AKHOME/final-verify"
rm -rf "$VERIFY"
mkdir -p "$VERIFY"

cd "$VERIFY"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img" >/dev/null

EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
ACTUAL=$(sha256sum kernel | awk '{print $1}')
SIZE=$(stat -c '%s' kernel)

echo "KERNEL SIZE : $SIZE"
echo "KERNEL SHA  : $ACTUAL"

if [ "$ACTUAL" != "$EXPECTED" ]; then
    echo "FAIL: FINAL KSU KERNEL SHA MISMATCH"
    exit 1
fi

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
