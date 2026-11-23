#!/bin/bash
set -e

ROOT="$HOME/kernel-source"
AK3="$ROOT/AnyKernel3"
OUT="$ROOT/output"
ZIP="$OUT/AnyKernel3-KSU-v0.9.2-certus.zip"

IMAGE="$ROOT/build/ksu-32915384-49/arch/arm64/boot/Image"
EXPECTED_IMAGE_SHA="3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238"

echo "============================================================"
echo "FINALIZE ANYKERNEL3 - KSU v0.9.2 / CERTUS"
echo "============================================================"

echo
echo "[1] VERIFY KSU IMAGE"

test -f "$IMAGE"

IMAGE_SHA=$(sha256sum "$IMAGE" | awk '{print $1}')
IMAGE_SIZE=$(stat -c '%s' "$IMAGE")

echo "SIZE : $IMAGE_SIZE"
echo "SHA  : $IMAGE_SHA"

if [ "$IMAGE_SHA" != "$EXPECTED_IMAGE_SHA" ]; then
    echo "FATAL: KSU Image SHA mismatch"
    exit 1
fi

echo "KSU IMAGE: PASS"

echo
echo "[2] VERIFY ANYKERNEL SCRIPT"

test -f "$AK3/anykernel.sh"

grep -q 'BLOCK=/dev/block/by-name/boot' "$AK3/anykernel.sh"
grep -q 'RAMDISK_COMPRESSION=auto' "$AK3/anykernel.sh"
grep -q 'PATCH_VBMETA_FLAG=auto' "$AK3/anykernel.sh"
grep -q 'dump_boot;' "$AK3/anykernel.sh"
grep -q 'write_boot;' "$AK3/anykernel.sh"

echo "ANYKERNEL SCRIPT: PASS"

echo
echo "[3] PREPARE CLEAN PACKAGE"

PKG="$OUT/ak3-final-package"

rm -rf "$PKG"
mkdir -p "$PKG/tools"

cp "$AK3/anykernel.sh" "$PKG/anykernel.sh"
cp -a "$AK3/META-INF" "$PKG/META-INF"
cp "$IMAGE" "$PKG/Image"

for f in \
    fec \
    httools_static \
    ak3-core.sh \
    magiskpolicy \
    magiskboot \
    busybox \
    snapshotupdater_static \
    lptools_static
do
    test -f "$AK3/tools/$f"
    cp "$AK3/tools/$f" "$PKG/tools/$f"
done

chmod 0755 "$PKG/anykernel.sh"
chmod 0755 "$PKG/tools/"*

echo "PACKAGE TREE:"
find "$PKG" -type f -printf '%P %s bytes\n' | sort

echo
echo "[4] STATIC SAFETY AUDIT"

echo "BLOCK:"
grep '^BLOCK=' "$PKG/anykernel.sh"

echo
echo "WRITE ENTRY:"
grep -nE 'dump_boot|write_boot|flash_boot' "$PKG/anykernel.sh"

echo
echo "DEVICE TARGET:"
grep -nE '/dev/block|boot' "$PKG/anykernel.sh"

echo
echo "[5] VERIFY MAGISKBOOT"

"$PKG/tools/magiskboot" --help >/dev/null 2>&1 || true

file "$PKG/tools/magiskboot"

echo
echo "[6] BUILD ZIP"

rm -f "$ZIP"

cd "$PKG"

zip -r -q -9 "$ZIP" .

echo "ZIP CREATED:"
stat -c '%n %s bytes' "$ZIP"

echo
echo "[7] ZIP CONTENTS"

unzip -l "$ZIP"

echo
echo "[8] VERIFY IMAGE INSIDE ZIP"

unzip -p "$ZIP" Image | sha256sum
unzip -p "$ZIP" Image | wc -c

ZIP_IMAGE_SHA=$(unzip -p "$ZIP" Image | sha256sum | awk '{print $1}')
ZIP_IMAGE_SIZE=$(unzip -p "$ZIP" Image | wc -c)

if [ "$ZIP_IMAGE_SHA" != "$EXPECTED_IMAGE_SHA" ]; then
    echo "FATAL: ZIP Image SHA mismatch"
    exit 1
fi

if [ "$ZIP_IMAGE_SIZE" != "$IMAGE_SIZE" ]; then
    echo "FATAL: ZIP Image size mismatch"
    exit 1
fi

echo "ZIP IMAGE: PASS"

echo
echo "[9] VERIFY ZIP INTEGRITY"

unzip -t "$ZIP"

echo
echo "[10] FINAL SHA256"

sha256sum "$ZIP"

echo
echo "============================================================"
echo "ANYKERNEL3 FINAL PACKAGE: PASS"
echo "============================================================"
echo "ZIP:"
echo "$ZIP"
echo
echo "KSU IMAGE SHA:"
echo "$EXPECTED_IMAGE_SHA"
echo
echo "NO FLASH PERFORMED."
