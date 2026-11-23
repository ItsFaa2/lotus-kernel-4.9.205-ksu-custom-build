#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib

BOOT = Path("/root/kernel-source/boot-lotus.img")
BUILD = Path("/root/kernel-source/build/ksu-32915384-49")
IMAGE = BUILD / "arch/arm64/boot/Image"
DTB = BUILD / "arch/arm64/boot/dts/mediatek/mt6765.dtb"

def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def align(value, alignment):
    return (value + alignment - 1) // alignment * alignment

def cstr(raw):
    return raw.split(b"\0", 1)[0]

data = BOOT.read_bytes()

print("=" * 64)
print("FAA BOOT REPACK FORENSIC V2")
print("=" * 64)

print("\n[FILES]")
print(f"BOOT : {BOOT}")
print(f"SIZE : {len(data):,}")
print(f"SHA  : {sha256_bytes(data)}")

print("\nIMAGE:")
print(f"PATH : {IMAGE}")
print(f"SIZE : {IMAGE.stat().st_size:,}")
print(f"SHA  : {sha256_file(IMAGE)}")

print("\nNEW DTB:")
print(f"PATH : {DTB}")
print(f"SIZE : {DTB.stat().st_size:,}")
print(f"SHA  : {sha256_file(DTB)}")

# Android boot image v0-v2 common header.
#
# struct boot_img_hdr:
#   magic[8]
#   kernel_size
#   kernel_addr
#   ramdisk_size
#   ramdisk_addr
#   second_size
#   second_addr
#   tags_addr
#   page_size
#   header_version
#   os_version
#   os_patch_level
#   name[16]
#   cmdline[512]
#   id[8]          (legacy field in this source format)
#
# Then v1/v2 extension fields.
#
# We parse the known offsets directly to avoid tuple-layout mistakes.

def u32(off):
    return struct.unpack_from("<I", data, off)[0]

def u64(off):
    return struct.unpack_from("<Q", data, off)[0]

magic = data[0:8]

kernel_size = u32(8)
kernel_addr = u32(12)

ramdisk_size = u32(16)
ramdisk_addr = u32(20)

second_size = u32(24)
second_addr = u32(28)

tags_addr = u32(32)

page_size = u32(36)
header_version = u32(40)

os_version = u32(44)
os_patch_level = u32(48)

name = data[52:68]
cmdline = data[68:580]

# v1/v2 fields used by this boot header.
# Original forensic values are expected:
# header_size = 1660
# dtb_size    = 110955
# dtb_addr    = 0x47880000
#
# Offsets are:
# header_size at 1580
# dtb_size    at 1584
# dtb_addr    at 1588
#
# However vendor/AOSP header layouts can differ, so print both
# candidate locations before trusting them.

candidate_1580 = u32(1580)
candidate_1584 = u32(1584)
candidate_1588_u32 = u32(1588)
candidate_1588_u64 = u64(1588)

print("\n[ORIGINAL HEADER CORE]")
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
print(f"name            : {cstr(name)!r}")
print(f"cmdline         : {cstr(cmdline)!r}")

print("\n[HEADER EXTENSION FORENSIC]")
print(f"u32 @ 1580       : {candidate_1580}")
print(f"u32 @ 1584       : {candidate_1584}")
print(f"u32 @ 1588       : {candidate_1588_u32}")
print(f"u64 @ 1588       : 0x{candidate_1588_u64:x}")

# Known values from previous exact boot forensic.
KNOWN_DTB_SIZE = 110955
KNOWN_DTB_ADDR = 0x47880000
KNOWN_HEADER_SIZE = 1660

# Determine DTB metadata using known Android v2 layout first.
#
# AOSP boot_img_hdr v2:
#   recovery_dtbo_size @ 1632
#   recovery_dtbo_offset @ 1640
#   header_size @ 1648
#   dtb_size @ 1652
#   dtb_addr @ 1656
#
# But this vendor image has previously been identified with:
#   header_size = 1660
#   dtb_size    = 110955
#   dtb_addr    = 0x47880000
#
# Therefore inspect all plausible locations and select the candidate
# matching the known exact DTB metadata.

candidates = []

for size_off, addr_off, hdr_off in [
    (1652, 1656, 1648),
    (1584, 1588, 1580),
]:
    if addr_off + 4 <= len(data):
        ds = u32(size_off)
        da = u64(addr_off) if addr_off + 8 <= len(data) else 0
        hs = u32(hdr_off)

        candidates.append((size_off, addr_off, hdr_off, ds, da, hs))

print("\n[CANDIDATE DTB METADATA]")

for c in candidates:
    size_off, addr_off, hdr_off, ds, da, hs = c
    print(
        f"size@{size_off}= {ds:,}, "
        f"addr@{addr_off}= 0x{da:x}, "
        f"header@{hdr_off}= {hs}"
    )

match = None

for c in candidates:
    size_off, addr_off, hdr_off, ds, da, hs = c
    if ds == KNOWN_DTB_SIZE and da == KNOWN_DTB_ADDR:
        match = c
        break

if match is None:
    raise SystemExit(
        "\nFATAL: could not identify DTB metadata safely. "
        "No image modification performed."
    )

size_off, addr_off, hdr_off, dtb_size, dtb_addr, header_size = match

print("\n[SELECTED VENDOR HEADER]")
print(f"header_size : {header_size}")
print(f"dtb_size    : {dtb_size:,}")
print(f"dtb_addr    : 0x{dtb_addr:x}")

if magic != b"ANDROID!":
    raise SystemExit("FATAL: invalid Android boot magic")

if page_size != 2048:
    raise SystemExit(f"FATAL: expected page size 2048, got {page_size}")

if header_version != 2:
    raise SystemExit(f"FATAL: expected header v2, got {header_version}")

if kernel_size == 0:
    raise SystemExit("FATAL: kernel_size is zero")

if ramdisk_size == 0:
    raise SystemExit("FATAL: ramdisk_size is zero")

if dtb_size == 0:
    raise SystemExit("FATAL: dtb_size is zero")

kernel_off = page_size
ramdisk_off = align(kernel_off + kernel_size, page_size)
second_off = align(ramdisk_off + ramdisk_size, page_size)
dtb_off = align(second_off + second_size, page_size)

print("\n[PAYLOAD OFFSETS]")
print(f"kernel : 0x{kernel_off:x}")
print(f"ramdisk: 0x{ramdisk_off:x}")
print(f"second : 0x{second_off:x}")
print(f"dtb    : 0x{dtb_off:x}")

if dtb_off + dtb_size > len(data):
    raise SystemExit("FATAL: DTB exceeds boot image")

ramdisk = data[ramdisk_off:ramdisk_off + ramdisk_size]
old_dtb = data[dtb_off:dtb_off + dtb_size]

out_ramdisk = BUILD / "original-ramdisk.bin"
out_dtb = BUILD / "original-dtb.bin"

out_ramdisk.write_bytes(ramdisk)
out_dtb.write_bytes(old_dtb)

print("\n[EXTRACTED RAMDISK]")
print(f"PATH   : {out_ramdisk}")
print(f"SIZE   : {len(ramdisk):,}")
print(f"SHA256 : {sha256_bytes(ramdisk)}")

print("\n[EXTRACTED ORIGINAL DTB]")
print(f"PATH   : {out_dtb}")
print(f"SIZE   : {len(old_dtb):,}")
print(f"SHA256 : {sha256_bytes(old_dtb)}")

print("\n[COMPARE NEW DTB]")
new_dtb = DTB.read_bytes()
print(f"NEW SIZE : {len(new_dtb):,}")
print(f"OLD SIZE : {len(old_dtb):,}")

print("\n[SAFETY]")
print("Original boot image modified : NO")
print("Original boot image SHA      :", sha256_file(BOOT))
print("Safe to proceed to repack    : YES")
