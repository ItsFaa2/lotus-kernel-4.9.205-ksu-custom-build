#!/usr/bin/env python3

import struct
import hashlib
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = {
    "stock": "boot-lotus.img",
    "folk": "boot-lotus-ksu-folk.img",
}

MAGICS = {
    "gzip": [
        b"\x1f\x8b\x08",
    ],
    "lz4": [
        b"\x02\x21\x4c\x18",
    ],
    "lzma": [
        b"\x5d\x00\x00",
    ],
    "xz": [
        b"\xfd7zXZ\x00",
    ],
    "bzip2": [
        b"BZh",
    ],
    "zstd": [
        b"\x28\xb5\x2f\xfd",
    ],
}

def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]

def align(x, a):
    return (x + a - 1) // a * a

def sha256(data):
    return hashlib.sha256(data).hexdigest()

for label, filename in FILES.items():
    data = (BASE / filename).read_bytes()

    page = u32(data, 0x24)
    kernel_size = u32(data, 0x08)

    kernel_off = page
    kernel = data[kernel_off:kernel_off + kernel_size]

    print("=" * 80)
    print(label.upper())
    print("=" * 80)

    print("SIZE :", len(kernel))
    print("SHA  :", sha256(kernel))
    print("FIRST 64 BYTES:")
    print(kernel[:64].hex(" "))

    print()
    print("COMPRESSION MAGIC:")

    found = False

    for name, signatures in MAGICS.items():
        for sig in signatures:
            positions = []
            start = 0

            while True:
                pos = kernel.find(sig, start)

                if pos < 0:
                    break

                positions.append(pos)
                start = pos + 1

            if positions:
                found = True
                print(
                    f"  {name:8} "
                    f"signature={sig.hex()} "
                    f"offsets={[hex(x) for x in positions[:20]]}"
                )

    if not found:
        print("  NO KNOWN COMPRESSION MAGIC")

    print()
    print("COMMON KERNEL MARKERS:")

    for marker in [
        b"Linux version",
        b"Linux",
        b"ARM",
        b"clang",
        b"gcc",
        b"KernelSU",
        b"KSU",
        b"LotusKernel",
        b"Folk",
    ]:
        pos = kernel.find(marker)

        if pos >= 0:
            print(f"  {marker!r} @ 0x{pos:x}")

    print()
