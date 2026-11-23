#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib

BOOT = Path("/root/kernel-source/boot-lotus.img")
BUILD = Path("/root/kernel-source/build/ksu-32915384-49")
IMAGE = BUILD / "arch/arm64/boot/Image"
DTB = BUILD / "arch/arm64/boot/dts/mediatek/mt6765.dtb"

PAGE = 2048

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def align(x, a):
    return (x + a - 1) // a * a

data = BOOT.read_bytes()

print("=" * 64)
print("FAA BOOT REPACK FORENSIC V1")
print("=" * 64)

print("\n[FILES]")
print(f"BOOT : {BOOT}")
print(f"SIZE : {len(data):,}")
print(f"SHA  : {sha256(BOOT)}")

print(f"\nIMAGE:")
print(f"PATH : {IMAGE}")
print(f"SIZE : {IMAGE.stat().st_size:,}")
print(f"SHA  : {sha256(IMAGE)}")

print(f"\nNEW DTB:")
print(f"PATH : {DTB}")
print(f"SIZE : {DTB.stat().st_size:,}")
print(f"SHA  : {sha256(DTB)}")

# Android boot image v2 header
fmt = "<8s10I16s512s32s"
size = struct.calcsize(fmt)

(
    magic,
    kernel_size,
    kernel_addr,
    ramdisk_size,
    ramdisk_addr,
    second_size,
    second_addr,
    tags_addr,
    page_size,
    header_version,
    os_version,
    os_patch_level,
    name,
    cmdline,
    id_field,
) = struct.unpack_from(fmt, data, 0)

# v2 additional fields
dtb_size = struct.unpack_from("<I", data, 1580)[0]
dtb_addr = struct.unpack_from("<Q", data, 1584)[0]
header_size = struct.unpack_from("<I", data, 1592)[0]

print("\n[ORIGINAL HEADER]")
print(f"magic           : {magic!r}")
print(f"kernel_size     : {kernel_size:,}")
print(f"kernel_addr     : 0x{kernel_addr:08x}")
print(f"ramdisk_size    : {ramdisk_size:,}")
print(f"ramdisk_addr    : 0x{ramdisk_addr:08x}")
print(f"second_size     : {second_size:,}")
print(f"second_addr     : 0x{second_addr:08x}")
print(f"tags_addr       : 0x{tags_addr:08x}")
print(f"page_size       : {page_size}")
print(f"header_version  : {header_version}")
print(f"os_version      : 0x{os_version:08x}")
print(f"os_patch_level  : 0x{os_patch_level:08x}")
print(f"name            : {name.rstrip(bytes([0]))!r}")
print(f"cmdline         : {cmdline.rstrip(bytes([0]))!r}")
print(f"dtb_size        : {dtb_size:,}")
print(f"dtb_addr        : 0x{dtb_addr:08x}")
print(f"header_size     : {header_size}")

# Locate payloads exactly as bootimg layout dictates.
off = page_size
kernel_off = off
ramdisk_off = align(kernel_off + kernel_size, page_size)
second_off = align(ramdisk_off + ramdisk_size, page_size)
dtb_off = align(second_off + second_size, page_size)

print("\n[PAYLOAD OFFSETS]")
print(f"kernel : 0x{kernel_off:x}")
print(f"ramdisk: 0x{ramdisk_off:x}")
print(f"second : 0x{second_off:x}")
print(f"dtb    : 0x{dtb_off:x}")

if magic != b"ANDROID!":
    raise SystemExit("FATAL: invalid Android boot magic")

if page_size != PAGE:
    raise SystemExit(f"FATAL: expected page size {PAGE}, got {page_size}")

if header_version != 2:
    raise SystemExit(f"FATAL: expected header v2, got {header_version}")

if ramdisk_size == 0:
    raise SystemExit("FATAL: ramdisk is empty")

if dtb_size == 0:
    raise SystemExit("FATAL: original DTB is empty")

if dtb_off + dtb_size > len(data):
    raise SystemExit("FATAL: DTB exceeds boot image")

ramdisk = data[ramdisk_off:ramdisk_off + ramdisk_size]
old_dtb = data[dtb_off:dtb_off + dtb_size]

out_ramdisk = BUILD / "original-ramdisk.bin"
out_dtb = BUILD / "original-dtb.bin"

out_ramdisk.write_bytes(ramdisk)
out_dtb.write_bytes(old_dtb)

print("\n[EXTRACTED]")
print(f"RAMDISK : {out_ramdisk}")
print(f"SIZE    : {len(ramdisk):,}")
print(f"SHA256  : {hashlib.sha256(ramdisk).hexdigest()}")

print(f"\nORIGINAL DTB : {out_dtb}")
print(f"SIZE         : {len(old_dtb):,}")
print(f"SHA256       : {hashlib.sha256(old_dtb).hexdigest()}")

print("\n[REPACK STATUS]")
print("SAFE TO PROCEED WITH mkbootimg: YES")
print("ORIGINAL BOOT IMAGE MODIFIED: NO")
