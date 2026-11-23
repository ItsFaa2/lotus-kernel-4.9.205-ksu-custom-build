#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib

BOOT = Path("/root/kernel-source/boot-lotus.img")
BUILD = Path("/root/kernel-source/build/ksu-32915384-49")
IMAGE = BUILD / "arch/arm64/boot/Image"

PAGE = 2048

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def align(x, a):
    return (x + a - 1) // a * a

data = BOOT.read_bytes()

print("=" * 64)
print("FAA BOOT REPACK FORENSIC V3")
print("=" * 64)

# ------------------------------------------------------------
# CORE BOOT HEADER
# ------------------------------------------------------------

magic = data[0:8]

if magic != b"ANDROID!":
    raise SystemExit("FATAL: invalid Android boot magic")

def u32(off):
    return struct.unpack_from("<I", data, off)[0]

def u64(off):
    return struct.unpack_from("<Q", data, off)[0]

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

name = data[52:68].split(b"\0", 1)[0]
cmdline = data[68:580].split(b"\0", 1)[0]

print("\n[BOOT]")
print(f"SIZE            : {len(data):,}")
print(f"SHA256          : {sha256(data)}")
print(f"MAGIC           : {magic!r}")
print(f"KERNEL SIZE     : {kernel_size:,}")
print(f"KERNEL ADDR     : 0x{kernel_addr:08x}")
print(f"RAMDISK SIZE    : {ramdisk_size:,}")
print(f"RAMDISK ADDR    : 0x{ramdisk_addr:08x}")
print(f"SECOND SIZE     : {second_size:,}")
print(f"SECOND ADDR     : 0x{second_addr:08x}")
print(f"TAGS ADDR       : 0x{tags_addr:08x}")
print(f"PAGE SIZE       : {page_size}")
print(f"HEADER VERSION  : {header_version}")
print(f"OS VERSION      : 0x{os_version:08x}")
print(f"OS PATCH LEVEL  : 0x{os_patch_level:08x}")
print(f"NAME            : {name!r}")
print(f"CMDLINE         : {cmdline!r}")

if page_size != PAGE:
    raise SystemExit(f"FATAL: unexpected page size: {page_size}")

if header_version != 2:
    raise SystemExit(f"FATAL: unexpected header version: {header_version}")

# ------------------------------------------------------------
# PAYLOAD OFFSETS
# ------------------------------------------------------------

kernel_off = PAGE
ramdisk_off = align(kernel_off + kernel_size, PAGE)
second_off = align(ramdisk_off + ramdisk_size, PAGE)

print("\n[PAYLOAD OFFSETS]")
print(f"KERNEL          : 0x{kernel_off:x}")
print(f"RAMDISK         : 0x{ramdisk_off:x}")
print(f"SECOND          : 0x{second_off:x}")

ramdisk_end = ramdisk_off + ramdisk_size

if ramdisk_end > len(data):
    raise SystemExit("FATAL: ramdisk exceeds boot image")

ramdisk = data[ramdisk_off:ramdisk_end]

ramdisk_out = BUILD / "original-ramdisk.bin"
ramdisk_out.write_bytes(ramdisk)

print("\n[RAMDISK]")
print(f"PATH            : {ramdisk_out}")
print(f"SIZE            : {len(ramdisk):,}")
print(f"SHA256          : {sha256(ramdisk)}")

# ------------------------------------------------------------
# DTB DISCOVERY BY FDT MAGIC
# ------------------------------------------------------------

# FDT magic is big-endian:
# 0xd00dfeed -> bytes d0 0d fe ed

FDT_MAGIC = b"\xd0\x0d\xfe\xed"

print("\n[DTB SEARCH]")
print(f"FDT MAGIC       : {FDT_MAGIC.hex()}")

hits = []
start = second_off

while True:
    pos = data.find(FDT_MAGIC, start)

    if pos < 0:
        break

    # Need at least FDT header.
    if pos + 40 <= len(data):
        totalsize = struct.unpack_from(">I", data, pos + 4)[0]
        version = struct.unpack_from(">I", data, pos + 20)[0]
        last_comp_version = struct.unpack_from(">I", data, pos + 24)[0]

        valid_size = (
            totalsize >= 40
            and totalsize <= len(data) - pos
        )

        if valid_size:
            hits.append(
                (pos, totalsize, version, last_comp_version)
            )

    start = pos + 4

if not hits:
    raise SystemExit("FATAL: no valid FDT found")

print(f"VALID FDT COUNT : {len(hits)}")

for i, (pos, totalsize, version, last_comp) in enumerate(hits):
    print(
        f"[{i}] offset=0x{pos:x} "
        f"size={totalsize:,} "
        f"version={version} "
        f"last_comp={last_comp}"
    )

# Prefer the FDT matching the previously observed DTB size.
preferred = None

for hit in hits:
    pos, totalsize, version, last_comp = hit

    if totalsize == 110955:
        preferred = hit
        break

if preferred is None:
    # If exactly one valid FDT exists, it is safe.
    if len(hits) == 1:
        preferred = hits[0]
    else:
        raise SystemExit(
            "FATAL: multiple FDTs found and no exact 110955-byte match"
        )

dtb_off, dtb_size, dtb_version, dtb_last_comp = preferred

dtb = data[dtb_off:dtb_off + dtb_size]

dtb_out = BUILD / "original-dtb.bin"
dtb_out.write_bytes(dtb)

print("\n[SELECTED ORIGINAL DTB]")
print(f"OFFSET          : 0x{dtb_off:x}")
print(f"SIZE            : {dtb_size:,}")
print(f"VERSION         : {dtb_version}")
print(f"SHA256          : {sha256(dtb)}")
print(f"PATH            : {dtb_out}")

# ------------------------------------------------------------
# PREVIOUSLY KNOWN VENDOR METADATA
# ------------------------------------------------------------

print("\n[VENDOR BOOT METADATA]")
print("HEADER SIZE     : 1660")
print("DTB SIZE        : 110955")
print("DTB ADDR        : 0x47880000")

# ------------------------------------------------------------
# NEW ARTIFACTS
# ------------------------------------------------------------

if not IMAGE.is_file():
    raise SystemExit("FATAL: new Image missing")

print("\n[NEW IMAGE]")
print(f"PATH            : {IMAGE}")
print(f"SIZE            : {IMAGE.stat().st_size:,}")
print(f"SHA256          : {sha256_file(IMAGE)}")

print("\n============================================================")
print("FORENSIC RESULT")
print("============================================================")
print("Original boot readable       : PASS")
print("Original ramdisk extracted   : PASS")
print("Original DTB located         : PASS")
print("New Image exists             : PASS")
print("Original boot modified       : NO")
print("Ready for controlled repack  : YES")
