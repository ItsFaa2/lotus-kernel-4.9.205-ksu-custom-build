#!/usr/bin/env python3

import hashlib
import struct
import re
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = {
    "stock": "boot-lotus.img",
    "folk": "boot-lotus-ksu-folk.img",
}

def u32le(data, off):
    return struct.unpack_from("<I", data, off)[0]

def align(x, a):
    return (x + a - 1) // a * a

def sha256(x):
    return hashlib.sha256(x).hexdigest()

for label, filename in FILES.items():
    data = (BASE / filename).read_bytes()

    page = u32le(data, 0x24)
    kernel_size = u32le(data, 0x08)
    ramdisk_size = u32le(data, 0x10)

    kernel_off = page
    ramdisk_off = kernel_off + align(kernel_size, page)

    kernel = data[kernel_off:kernel_off + kernel_size]

    print("=" * 80)
    print(label.upper())
    print("=" * 80)

    print("KERNEL SIZE :", len(kernel))
    print("KERNEL SHA  :", sha256(kernel))

    print()
    print("[ARM64 IMAGE HEADER]")

    # ARM64 Linux Image header:
    # 0x00: code0
    # 0x04: code1
    # 0x08: text_offset
    # 0x10: image_size
    # 0x18: flags
    # 0x38: magic "ARM\x64"
    # 0x3c: res2
    if len(kernel) >= 0x40:
        code0 = u32le(kernel, 0x00)
        code1 = u32le(kernel, 0x04)
        text_offset = struct.unpack_from("<Q", kernel, 0x08)[0]
        image_size = struct.unpack_from("<Q", kernel, 0x10)[0]
        flags = struct.unpack_from("<Q", kernel, 0x18)[0]
        magic = kernel[0x38:0x3c]

        print(f"code0       : 0x{code0:08x}")
        print(f"code1       : 0x{code1:08x}")
        print(f"text_offset : 0x{text_offset:x}")
        print(f"image_size  : 0x{image_size:x} ({image_size:,})")
        print(f"flags       : 0x{flags:x}")
        print(f"magic       : {magic!r}")

        if magic == b"ARMd":
            print("IMAGE TYPE  : ARM64 Linux Image")
        else:
            print("IMAGE TYPE  : MAGIC MISMATCH")

    print()
    print("[KERNEL STRINGS]")

    blob = kernel

    patterns = [
        rb"Linux version [^\x00\n]{1,300}",
        rb"gcc version [^\x00\n]{1,300}",
        rb"clang version [^\x00\n]{1,300}",
        rb"LLVM version [^\x00\n]{1,300}",
        rb"LotusKernel[^\x00\n]{0,200}",
        rb"KernelSU[^\x00\n]{0,200}",
        rb"KSU[^\x00\n]{0,200}",
        rb"Folk[^\x00\n]{0,200}",
    ]

    found = set()

    for pattern in patterns:
        for match in re.finditer(pattern, blob):
            text = match.group().decode("utf-8", "replace")

            key = text[:500]

            if key not in found:
                found.add(key)
                print(text)

    if not found:
        print("NO RELEVANT STRINGS FOUND")

    print()
    print("[KERNEL DIFFERENCE SIZE]")
    print()
