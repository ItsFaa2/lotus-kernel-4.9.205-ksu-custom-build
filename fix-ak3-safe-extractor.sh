#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
CORE="$AK3/tools/ak3-core.sh"
AKHOME="$ROOT/output/ak3-literal-test/work"
BIN="$AK3/tools"

echo "============================================================"
echo "FIX AK3 SAFE FLASH_BOOT EXTRACTOR"
echo "============================================================"

cd "$AKHOME"

python3 - "$CORE" "$AKHOME/ak3-safe-flashboot.sh" <<'PY'
import sys

src_path = sys.argv[1]
out_path = sys.argv[2]

src = open(src_path, "r", encoding="utf-8").read()

# Exact function boundaries from ak3-core.sh.
start_marker = "flash_boot() {"
end_marker = "\n  }\n\n# flash_generic"

start = src.index(start_marker)
end = src.index(end_marker, start) + len("\n  }")

func = src[start:end]

print("FUNCTION START :", start)
print("FUNCTION END   :", end)
print("FUNCTION SIZE  :", len(func))

# Exact real-write section from the source shown in forensic output.
write_start_marker = "    blockdev --setrw $BLOCK"
write_end_marker = (
    "    if [ $? != 0 ]; then\n"
    "      abort \"Flashing image failed. Aborting...\";\n"
    "    fi;"
)

write_start = func.index(write_start_marker)
write_end = func.index(write_end_marker, write_start) + len(write_end_marker)

print("WRITE START    :", write_start)
print("WRITE END      :", write_end)

safe_write = """    echo "============================================================";
    echo "SAFE MODE: BLOCK WRITE SUPPRESSED";
    echo "SAFE MODE: boot-new.img already built";
    echo "SAFE MODE: no blockdev/dd/cat/nandwrite executed";
    echo "============================================================";
    return 0;"""

safe_func = (
    func[:write_start]
    + safe_write
    + func[write_end:]
)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(safe_func + "\n")

print("SAFE FUNCTION CREATED")
PY

echo
echo "[1] VERIFY SAFE FUNCTION"

grep -nE \
    'SAFE MODE|blockdev --setrw|nandwrite|dd if=|cat boot-new.img' \
    "$AKHOME/ak3-safe-flashboot.sh" || true

echo
echo "[2] VERIFY FUNCTION BOUNDARY"

grep -nE \
    '^flash_boot\(\)|SAFE MODE|^  \}' \
    "$AKHOME/ak3-safe-flashboot.sh"

echo
echo "[3] SOURCE SAFE FUNCTION"

source "$AKHOME/ak3-safe-flashboot.sh"

declare -F flash_boot

echo
echo "[4] EXECUTE"

cd "$AKHOME"

export AKHOME
export BIN="$AK3/tools"
export BOOTIMG="$AKHOME/boot.img"
export SPLITIMG="$AKHOME/split_img"
export RAMDISK_COMPRESSION=auto
export PATCH_VBMETA_FLAG=auto
export NO_MAGISK_CHECK=1
export OUTFD=1
export PATH="$BIN:$PATH"

flash_boot

echo
echo "============================================================"
echo "RESULT"
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
echo "[5] FINAL BOOT FORENSIC"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img"

echo
echo "[6] VERIFY KSU PAYLOAD"

VERIFY="$AKHOME/final-verify"
rm -rf "$VERIFY"
mkdir -p "$VERIFY"

cd "$VERIFY"

"$BIN/magiskboot" unpack -h "$AKHOME/boot-new.img" >/dev/null

KSU_SHA_EXPECTED="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"
KSU_SHA_ACTUAL=$(sha256sum kernel | awk '{print $1}')

echo "KERNEL SIZE : $(stat -c '%s' kernel)"
echo "KERNEL SHA  : $KSU_SHA_ACTUAL"

if [ "$KSU_SHA_ACTUAL" != "$KSU_SHA_EXPECTED" ]; then
    echo "FAIL: KSU kernel SHA mismatch"
    exit 1
fi

echo
echo "============================================================"
echo "AK3 SAFE FLASH_BOOT: PASS"
echo "============================================================"
echo "NO REAL BLOCK DEVICE WAS WRITTEN."
