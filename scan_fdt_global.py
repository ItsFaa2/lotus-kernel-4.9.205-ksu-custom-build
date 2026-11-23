#!/usr/bin/env python3

import struct
import hashlib
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = [
    "boot-lotus.img",
    "boot-lotus-ksu-folk.img",
    "kitsune-magisk_patched-30710_guVWi.img",
]

FDT_MAGIC = bytes.fromhex("d00dfeed")
MTK_MAGIC = bytes.fromhex("d7b7ab1e")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def u32be(data, off):
    return struct.unpack_from(">I", data, off)[0]


for name in FILES:
    path = BASE / name
    data = path.read_bytes()

    print("=" * 80)
    print(name)
    print("=" * 80)

    # Scan all FDT magic occurrences.
    fdt_positions = []
    pos = 0

    while True:
        pos = data.find(FDT_MAGIC, pos)

        if pos < 0:
            break

        fdt_positions.append(pos)
        pos += 1

    print(f"FDT MAGIC COUNT : {len(fdt_positions)}")

    for i, off in enumerate(fdt_positions, 1):
        print()
        print(f"[FDT {i}] OFFSET : 0x{off:x}")

        if off + 8 > len(data):
            print("  TRUNCATED HEADER")
            continue

        totalsize = u32be(data, off + 4)

        print(f"  TOTALSIZE      : {totalsize:,}")
        print(f"  END            : 0x{off + totalsize:x}")

        if totalsize <= 0:
            print("  INVALID SIZE")
            continue

        if off + totalsize > len(data):
            print("  INVALID: extends beyond image")
            continue

        fdt = data[off:off + totalsize]

        print(f"  SHA256         : {sha256(fdt)}")

        # Standard FDT header fields.
        if off + 40 <= len(data):
            magic = u32be(data, off)
            totalsize = u32be(data, off + 4)
            off_dt_struct = u32be(data, off + 8)
            off_dt_strings = u32be(data, off + 12)
            off_mem_rsvmap = u32be(data, off + 16)
            version = u32be(data, off + 20)
            last_comp_version = u32be(data, off + 24)
            boot_cpuid_phys = u32be(data, off + 28)
            size_dt_strings = u32be(data, off + 32)
            size_dt_struct = u32be(data, off + 36)

            print(f"  MAGIC          : 0x{magic:08x}")
            print(f"  VERSION        : {version}")
            print(f"  LAST VERSION   : {last_comp_version}")
            print(f"  STRUCT SIZE    : {size_dt_struct:,}")
            print(f"  STRINGS SIZE   : {size_dt_strings:,}")

    print()

    # Scan MTK wrapper globally too.
    mtk_positions = []
    pos = 0

    while True:
        pos = data.find(MTK_MAGIC, pos)

        if pos < 0:
            break

        mtk_positions.append(pos)
        pos += 1

    print(f"MTK MAGIC COUNT  : {len(mtk_positions)}")

    for off in mtk_positions:
        print(f"  MTK OFFSET      : 0x{off:x}")

    print()
