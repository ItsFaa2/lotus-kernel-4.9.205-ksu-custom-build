#!/bin/bash
set -e

AK3="$HOME/kernel-source/AnyKernel3"
PKG="$HOME/kernel-source/output/AnyKernel3-KSU-v0.9.2-certus"
STOCK="$HOME/kernel-source/boot-lotus.img"
TEST="$HOME/kernel-source/output/ak3-test"

rm -rf "$TEST"
mkdir -p "$TEST"

echo "============================================================"
echo "AK3 KSU v0.9.2 STATIC FORENSIC"
echo "============================================================"

echo
echo "[1] PACKAGE"
test -f "$PKG/anykernel.sh"
test -f "$PKG/Image"

sha256sum "$PKG/Image"
stat -c '%n %s bytes' "$PKG/Image"

echo
echo "[2] STOCK BOOT"
sha256sum "$STOCK"
stat -c '%n %s bytes' "$STOCK"

echo
echo "[3] PREPARE SIMULATION"
cp "$STOCK" "$TEST/boot.img"

cd "$TEST"

echo
echo "[4] MAGISKBOOT UNPACK"
"$AK3/tools/magiskboot" unpack -h boot.img

echo
echo "[5] STOCK PAYLOAD"
sha256sum kernel kernel_dtb ramdisk.cpio dtb
stat -c '%n %s bytes' kernel kernel_dtb ramdisk.cpio dtb

echo
echo "[6] REPLACE KERNEL WITH KSU"
cp "$PKG/Image" kernel

echo "KSU KERNEL:"
sha256sum kernel
stat -c '%n %s bytes' kernel

echo
echo "[7] RECOMPRESS KERNEL"
"$AK3/tools/magiskboot" compress=gzip kernel kernel.gz

echo
echo "[8] KERNEL GZIP"
file kernel.gz
stat -c '%n %s bytes' kernel.gz
sha256sum kernel.gz

echo
echo "[9] NOTE"
echo "This is the payload replacement test."
echo "No boot partition write."
echo "No device interaction."

echo
echo "============================================================"
echo "STATIC FORENSIC PASS"
echo "============================================================"
