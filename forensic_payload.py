#!/usr/bin/env python3

import hashlib
import struct
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = [
    "boot-lotus.img",
    "boot-lotus-ksu-folk.img",
    "kitsune-magisk_patched-30710_guVWi.img",
    "Lotus-Kitsune_boot.img",
]


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def align(value, alignment):
    return (value + alignment - 1) // alignment * alignment


print("=" * 80)
print("FAA BOOT PAYLOAD FORENSIC V2")
print("=" * 80)

for filename in FILES:
    path = BASE / filename

    print()
    print("=" * 80)
    print(filename)
    print("=" * 80)

    if not path.exists():
        print("STATUS: MISSING")
        print(f"PATH  : {path}")
        continue

    data = path.read_bytes()

    if len(data) < 0x678:
        print("STATUS: TOO SMALL")
        continue

    print(f"SIZE            : {len(data):,}")
    print(f"FULL SHA256     : {sha256(data)}")
    print(f"MAGIC           : {data[:8]!r}")

    if data[:8] != b"ANDROID!":
        print("STATUS          : INVALID ANDROID BOOT IMAGE")
        continue

    kernel_size = u32(data, 0x08)
    ramdisk_size = u32(data, 0x10)
    second_size = u32(data, 0x18)
    page_size = u32(data, 0x24)
    header_version = u32(data, 0x28)
    os_version = u32(data, 0x2c)

    kernel_off = page_size
    ramdisk_off = kernel_off + align(kernel_size, page_size)
    second_off = ramdisk_off + align(ramdisk_size, page_size)

    dtb_addr = u32(data, 0x670)
    dtb_size = u32(data, 0x674)

    dtb_off = second_off + align(second_size, page_size)

    kernel = data[
        kernel_off:
        kernel_off + kernel_size
    ]

    ramdisk = data[
        ramdisk_off:
        ramdisk_off + ramdisk_size
    ]

    dtb = data[
        dtb_off:
        dtb_off + dtb_size
    ]

    cmdline = data[0x40:0x40 + 512].split(b"\0", 1)[0]

    print()
    print(f"KERNEL SIZE     : {kernel_size:,}")
    print(f"KERNEL OFFSET   : 0x{kernel_off:x}")
    print(f"KERNEL END      : 0x{kernel_off + kernel_size:x}")
    print(f"KERNEL SHA256   : {sha256(kernel)}")

    print()
    print(f"RAMDISK SIZE    : {ramdisk_size:,}")
    print(f"RAMDISK OFFSET  : 0x{ramdisk_off:x}")
    print(f"RAMDISK END     : 0x{ramdisk_off + ramdisk_size:x}")
    print(f"RAMDISK SHA256  : {sha256(ramdisk)}")

    print()
    print(f"SECOND SIZE     : {second_size:,}")
    print(f"SECOND OFFSET   : 0x{second_off:x}")

    print()
    print(f"DTB ADDR        : 0x{dtb_addr:08x}")
    print(f"DTB SIZE        : {dtb_size:,}")
    print(f"DTB OFFSET      : 0x{dtb_off:x}")
    print(f"DTB END         : 0x{dtb_off + dtb_size:x}")

    if len(dtb) != dtb_size:
        print(f"DTB READ        : ERROR expected={dtb_size:,} got={len(dtb):,}")
    else:
        print(f"DTB MAGIC       : {dtb[:4].hex()}")
        print(f"DTB SHA256      : {sha256(dtb)}")

        if dtb[:4] == bytes.fromhex("d00dfeed"):
            print("DTB TYPE        : RAW FDT")
        elif dtb[:4] == bytes.fromhex("d7b7ab1e"):
            print("DTB TYPE        : MTK WRAPPER")
        else:
            print("DTB TYPE        : UNKNOWN")

    print()
    print(f"PAGE SIZE       : {page_size}")
    print(f"HEADER VERSION  : {header_version}")
    print(f"OS VERSION      : 0x{os_version:08x}")
    print(f"CMDLINE         : {cmdline.decode(errors='replace')}")

print()
print("=" * 80)
print("END")
print("=" * 80)
