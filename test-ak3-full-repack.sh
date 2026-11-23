#!/bin/bash
set -e

AK3="$HOME/kernel-source/AnyKernel3"
KSU="$HOME/kernel-source/build/ksu-32915384-49/arch/arm64/boot/Image"
STOCK="$HOME/kernel-source/boot-lotus.img"
OUT="$HOME/kernel-source/output/ak3-full-test"

rm -rf "$OUT"
mkdir -p "$OUT"
cd "$OUT"

cp "$STOCK" original.img

echo "============================================================"
echo "1. UNPACK STOCK"
echo "============================================================"

"$AK3/tools/magiskboot" unpack -h original.img

echo
echo "============================================================"
echo "2. REPLACE KERNEL"
echo "============================================================"

cp "$KSU" kernel

sha256sum kernel
stat -c '%n %s bytes' kernel

echo
echo "============================================================"
echo "3. REPACK KSU BOOT"
echo "============================================================"

"$AK3/tools/magiskboot" repack original.img ksu-repacked.img

echo
echo "============================================================"
echo "4. IMAGE RESULT"
echo "============================================================"

stat -c '%n %s bytes' original.img ksu-repacked.img
sha256sum original.img ksu-repacked.img

echo
echo "============================================================"
echo "5. FORENSIC KSU IMAGE"
echo "============================================================"

rm -f kernel kernel_dtb ramdisk.cpio dtb header

"$AK3/tools/magiskboot" unpack -h ksu-repacked.img

echo
echo "HEADER:"
cat header

echo
echo "COMPONENTS:"
for f in kernel kernel_dtb ramdisk.cpio dtb; do
    echo
    echo "[$f]"
    file "$f"
    stat -c '%n %s bytes' "$f"
    sha256sum "$f"
done

echo
echo "============================================================"
echo "6. AUTOMATED INTEGRITY CHECK"
echo "============================================================"

KERNEL_SHA="$(sha256sum kernel | awk '{print $1}')"
KERNEL_SIZE="$(stat -c '%s' kernel)"
RAMDISK_SHA="$(sha256sum ramdisk.cpio | awk '{print $1}')"
DTB_SHA="$(sha256sum dtb | awk '{print $1}')"
KERNEL_DTB_SHA="$(sha256sum kernel_dtb | awk '{print $1}')"
IMAGE_SIZE="$(stat -c '%s' ksu-repacked.img)"

PASS=1

[ "$KERNEL_SHA" = "3868f4d3e75a670aaf2e623f22dc939174e5e30351db4c7c57aa04c8ea803238" ] || {
    echo "FAIL: KERNEL SHA"
    PASS=0
}

[ "$KERNEL_SIZE" = "33943572" ] || {
    echo "FAIL: KERNEL SIZE"
    PASS=0
}

[ "$RAMDISK_SHA" = "1a592696fd37b76550f5e7bdedd2b74e634166064d8d6ba5fc5c28d8fb6b9d8a" ] || {
    echo "FAIL: RAMDISK"
    PASS=0
}

[ "$DTB_SHA" = "156c9b956f25edf1e25e75454828f893b1f1d205edb25528eedeea48fb94c76a" ] || {
    echo "FAIL: DTB"
    PASS=0
}

[ "$KERNEL_DTB_SHA" = "702f1e3839cceac8dc420c027a7a242c39a4bbe5b6f60bbd55f3e148183fc56f" ] || {
    echo "FAIL: KERNEL_DTB"
    PASS=0
}

[ "$IMAGE_SIZE" -le 67108864 ] || {
    echo "FAIL: IMAGE > 64 MiB"
    PASS=0
}

grep -q 'HEADER_VER.*\[2\]' header || {
    echo "FAIL: HEADER VERSION"
    PASS=0
}

grep -q 'PAGESIZE.*\[2048\]' header || {
    echo "FAIL: PAGE SIZE"
    PASS=0
}

grep -q 'KERNEL_FMT.*\[gzip\]' header || {
    echo "FAIL: KERNEL COMPRESSION"
    PASS=0
}

grep -q 'RAMDISK_FMT.*\[gzip\]' header || {
    echo "FAIL: RAMDISK COMPRESSION"
    PASS=0
}

if [ "$PASS" -eq 1 ]; then
    echo
    echo "============================================================"
    echo "FULL KSU BOOT REPACK: PASS"
    echo "============================================================"
    echo
    echo "OUTPUT:"
    echo "$OUT/ksu-repacked.img"
    echo
    echo "SHA256:"
    sha256sum ksu-repacked.img
else
    echo
    echo "FULL KSU BOOT REPACK: FAIL"
    exit 1
fi
