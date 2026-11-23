#!/usr/bin/env python3

import struct
from pathlib import Path

BASE = Path.home() / "kernel-source"

FILES = [
    "boot-lotus.img",
    "boot-lotus-ksu-folk.img",
]

FIELDS = {
    "kernel_size": 0x08,
    "ramdisk_size": 0x10,
    "second_size": 0x18,
    "kernel_addr": 0x0c,
    "ramdisk_addr": 0x14,
    "second_addr": 0x1c,
    "tags_addr": 0x20,
    "page_size": 0x24,
    "header_version": 0x28,
    "os_version": 0x2c,
    "dtb_addr": 0x670,
    "dtb_size": 0x674,
}

def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]

def read_cmdline(data):
    raw = data[0x40:0x40 + 512]
    return raw.split(b"\0", 1)[0].decode(errors="replace")

images = {}

for name in FILES:
    data = (BASE / name).read_bytes()
    images[name] = data

    print("=" * 80)
    print(name)
    print("=" * 80)

    print(f"SIZE       : {len(data):,}")
    print(f"MAGIC      : {data[:8]!r}")

    for field, off in FIELDS.items():
        print(f"{field:15}: 0x{u32(data, off):08x} ({u32(data, off):,})")

    print(f"{'cmdline':15}: {read_cmdline(data)}")

print()
print("=" * 80)
print("HEADER COMPARISON")
print("=" * 80)

a = images[FILES[0]]
b = images[FILES[1]]

all_match = True

for field, off in FIELDS.items():
    va = u32(a, off)
    vb = u32(b, off)

    same = va == vb

    print(
        f"{field:15}: "
        f"{'MATCH' if same else 'DIFF'} "
        f"stock=0x{va:08x} "
        f"ksu=0x{vb:08x}"
    )

    if not same:
        all_match = False

ca = read_cmdline(a)
cb = read_cmdline(b)

print(
    f"{'cmdline':15}: "
    f"{'MATCH' if ca == cb else 'DIFF'}"
)

if ca != cb:
    all_match = False

print()
print(
    "HEADER VERDICT : "
    + ("PASS" if all_match else "DIFF FOUND")
)
