#!/usr/bin/env python3

import gzip
import hashlib
import struct
import re
from pathlib import Path

BASE = Path.home() / "kernel-source"
OUT = BASE / "kernel-forensic"
OUT.mkdir(exist_ok=True)

FILES = {
    "stock": "boot-lotus.img",
    "folk": "boot-lotus-ksu-folk.img",
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

    kernel = data[page:page + kernel_size]

    print("=" * 80)
    print(label.upper())
    print("=" * 80)

    print("COMPRESSED SIZE :", len(kernel))
    print("COMPRESSED SHA  :", sha256(kernel))

    try:
        decompressed = gzip.decompress(kernel)
    except Exception as e:
        print("GZIP DECOMPRESS : FAILED")
        print("ERROR           :", e)
        continue

    out = OUT / f"{label}-kernel.raw"
    out.write_bytes(decompressed)

    print("RAW SIZE        :", len(decompressed))
    print("RAW SHA256      :", sha256(decompressed))
    print("OUTPUT          :", out)

    print()
    print("[KERNEL RELEASE STRINGS]")

    patterns = [
        rb"Linux version [^\x00\n]{1,300}",
        rb"gcc version [^\x00\n]{1,300}",
        rb"clang version [^\x00\n]{1,300}",
        rb"LLVM version [^\x00\n]{1,300}",
        rb"CONFIG_LOCALVERSION[^\x00\n]{0,100}",
        rb"KernelSU[^\x00\n]{0,200}",
        rb"FolkPatch[^\x00\n]{0,200}",
        rb"LotusKernel[^\x00\n]{0,200}",
    ]

    found = set()

    for pattern in patterns:
        for match in re.finditer(pattern, decompressed):
            text = match.group().decode("utf-8", "replace")

            if text not in found:
                found.add(text)
                print(text)

    if not found:
        print("NO MATCH")

    print()
    print("[KNOWN MARKERS]")

    for marker in [
        b"KernelSU",
        b"kernelsu",
        b"KSU",
        b"ksud",
        b"FolkPatch",
        b"Folk",
        b"LotusKernel",
        b"LotusKernel-OSS",
    ]:
        positions = []
        start = 0

        while True:
            pos = decompressed.find(marker, start)

            if pos < 0:
                break

            positions.append(pos)
            start = pos + 1

        if positions:
            print(
                f"{marker!r}: "
                f"{len(positions)} matches, "
                f"first={[hex(x) for x in positions[:10]]}"
            )

    print()
