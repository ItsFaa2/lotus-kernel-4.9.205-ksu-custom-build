#!/usr/bin/env python3

import struct
import hashlib
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = {
    "stock": "boot-lotus.img",
    "folk": "boot-lotus-ksu-folk.img",
}

def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]

def align(x, a):
    return (x + a - 1) // a * a

for label, filename in FILES.items():
    data = (BASE / filename).read_bytes()

    kernel_size = u32(data, 0x08)
    ramdisk_size = u32(data, 0x10)
    page_size = u32(data, 0x24)

    kernel_off = page_size
    ramdisk_off = kernel_off + align(kernel_size, page_size)

    kernel = data[kernel_off:kernel_off + kernel_size]
    ramdisk = data[ramdisk_off:ramdisk_off + ramdisk_size]

    print("=" * 80)
    print(label.upper())
    print("=" * 80)

    print("IMAGE SHA256 :", hashlib.sha256(data).hexdigest())
    print("KERNEL SIZE  :", kernel_size)
    print("KERNEL SHA256:", hashlib.sha256(kernel).hexdigest())
    print("RAMDISK SHA256:", hashlib.sha256(ramdisk).hexdigest())

    # Linux ARM64 Image magic:
    # offset 0x38 contains "ARMd" for Image
    if len(kernel) >= 0x40:
        magic = kernel[0x38:0x3c]
        print("IMAGE MAGIC  :", magic)

        text = kernel[:2 * 1024 * 1024]

        for needle in [
            b"Linux version ",
            b"LotusKernel",
            b"KernelSU",
            b"KSU",
            b"Folk",
        ]:
            pos = text.find(needle)
            if pos >= 0:
                start = max(0, pos - 80)
                end = min(len(text), pos + 300)
                chunk = text[start:end]

                print()
                print(f"FOUND {needle!r} @ 0x{pos:x}")
                print(chunk.decode("utf-8", "replace"))
