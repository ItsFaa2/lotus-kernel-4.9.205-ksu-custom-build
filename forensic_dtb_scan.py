#!/usr/bin/env python3

import hashlib
import struct
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = [
    "boot-lotus.img",
    "boot-lotus-ksu-folk.img",
    "kitsune-magisk_patched-30710_guVWi.img",
]

MAGIC_MTK = bytes.fromhex("d7b7ab1e")
MAGIC_FDT = bytes.fromhex("d00dfeed")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def u32be(data, off):
    return struct.unpack_from(">I", data, off)[0]


def u32le(data, off):
    return struct.unpack_from("<I", data, off)[0]


for name in FILES:
    path = BASE / name

    print("=" * 80)
    print(name)
    print("=" * 80)

    data = path.read_bytes()

    print(f"SIZE       : {len(data):,}")
    print(f"SHA256     : {sha256(data)}")

    positions = []
    start = 0

    while True:
        pos = data.find(MAGIC_MTK, start)

        if pos < 0:
            break

        positions.append(pos)
        start = pos + 1

    print(f"MTK MAGIC COUNT: {len(positions)}")

    for pos in positions:
        print()
        print(f"MTK WRAPPER OFFSET : 0x{pos:x}")

        if pos + 64 > len(data):
            print("TRUNCATED HEADER")
            continue

        header = data[pos:pos + 64]

        print(f"HEADER HEX         : {header.hex(' ')}")

        # Known MTK wrapper layout observed on this device:
        # +0x00 magic
        # +0x04 version / header field
        # +0x08 total size
        # +0x0c payload size / related field
        # Actual FDT is normally immediately after the wrapper header.

        candidates = []

        for off in range(pos, min(pos + 128, len(data) - 4), 4):
            if data[off:off + 4] == MAGIC_FDT:
                candidates.append(off)

        if candidates:
            for fdt_pos in candidates:
                print(f"FDT MAGIC OFFSET     : 0x{fdt_pos:x}")

                if fdt_pos + 8 <= len(data):
                    fdt_size = u32be(data, fdt_pos + 4)

                    print(f"FDT SIZE            : {fdt_size:,}")

                    fdt_end = fdt_pos + fdt_size

                    print(f"FDT END             : 0x{fdt_end:x}")

                    if fdt_end <= len(data):
                        fdt = data[fdt_pos:fdt_end]

                        print(f"FDT SHA256          : {sha256(fdt)}")
                    else:
                        print("FDT END             : OUT OF IMAGE")
        else:
            print("FDT MAGIC            : NOT FOUND NEAR WRAPPER")

    print()
