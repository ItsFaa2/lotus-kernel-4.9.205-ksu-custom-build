#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
KSU="$ROOT/build/ksu-32915384-49/arch/arm64/boot/Image"
STOCK="$ROOT/boot-lotus.img"
OUT="$ROOT/output/ak3-dryrun"

rm -rf "$OUT"
mkdir -p "$OUT"

echo "============================================================"
echo "AK3 v0.9.2 DRY-RUN"
echo "============================================================"

echo
echo "[1] PREPARE SANDBOX"

cp "$STOCK" "$OUT/boot-stock.img"

# Create isolated AK3 package copy.
rm -rf "$OUT/AnyKernel3"
cp -a "$AK3" "$OUT/AnyKernel3"

cd "$OUT/AnyKernel3"

# Replace kernel payload.
cp "$KSU" Image

# Redirect BLOCK to a regular sandbox file.
python3 - <<'PY'
from pathlib import Path

p = Path("anykernel.sh")
s = p.read_text()

s = s.replace(
    'BLOCK=/dev/block/by-name/boot;',
    'BLOCK="$HOME/kernel-source/output/ak3-dryrun/boot-ak3-output.img";'
)

p.write_text(s)
PY

echo "AK3 sandbox:"
pwd

echo
echo "[2] VERIFY PAYLOAD"

sha256sum Image
stat -c '%n %s bytes' Image

echo
echo "[3] INSPECT AK3 CORE"

grep -nE '^(split_boot|dump_boot|flash_boot|write_boot|repack_ramdisk)' \
    tools/ak3-core.sh || true

echo
echo "[4] CREATE BOOT SOURCE"

cp "$STOCK" boot-source.img

# Override the boot image source expected by AK3.
python3 - <<'PY'
from pathlib import Path

p = Path("anykernel.sh")
s = p.read_text()

# AK3's dump_boot normally discovers the boot block.
# Force the sandbox image instead.
s = s.replace(
    'BLOCK="$HOME/kernel-source/output/ak3-dryrun/boot-ak3-output.img";',
    'BLOCK="$HOME/kernel-source/output/ak3-dryrun/boot-ak3-output.img";\nBOOT_IMAGE="$HOME/kernel-source/output/ak3-dryrun/boot-source.img";'
)

p.write_text(s)
PY

echo
echo "[5] IMPORTANT"
echo "This script will NOT be executed blindly."
echo "Inspecting AK3 flash_boot/write_boot implementation first."

echo
echo "============================================================"
echo "AK3 DRY-RUN PREPARED"
echo "============================================================"
echo
echo "SANDBOX:"
echo "$OUT/AnyKernel3"
echo
echo "STOCK:"
echo "$OUT/boot-stock.img"
echo
echo "KSU:"
echo "$KSU"
