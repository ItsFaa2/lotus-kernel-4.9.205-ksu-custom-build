#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib

BUILD = Path("/root/kernel-source/build/ksu-32915384-49")

NEW_DTB = BUILD / "arch/arm64/boot/dts/mediatek/mt6765.dtb"
OUT = BUILD / "mtk-dtb-wrapper.bin"

MAGIC = 0xD7B7AB1E
WRAPPER_SIZE = 64

def sha256(data):
    return hashlib.sha256(data).hexdigest()

dtb = NEW_DTB.read_bytes()

if len(dtb) < 40:
    raise SystemExit("FATAL: DTB terlalu kecil")

magic = struct.unpack_from(">I", dtb, 0)[0]
totalsize = struct.unpack_from(">I", dtb, 4)[0]

print("=" * 64)
print("FAA MTK DTB WRAPPER BUILD V1")
print("=" * 64)

print(f"DTB PATH : {NEW_DTB}")
print(f"DTB SIZE : {len(dtb):,}")
print(f"DTB SHA  : {sha256(dtb)}")
print(f"FDT MAGIC: 0x{magic:08x}")
print(f"FDT SIZE : {totalsize:,}")

if magic != 0xD00DFEED:
    raise SystemExit("FATAL: bukan valid FDT")

if totalsize != len(dtb):
    raise SystemExit(
        f"FATAL: FDT totalsize {totalsize} != file size {len(dtb)}"
    )

# MTK DTB wrapper observed from original boot:
#
# +00 magic          BE u32
# +04 total_size     BE u32
# +08 0x20           BE u32
# +0c 0x20           BE u32
# +10 0x01           BE u32
# +14 0x20           BE u32
# +18 0x800          BE u32
# +1c 0              BE u32
# +20 payload_size   BE u32
# +24 0x40           BE u32
# +28..3c zero
#
# Original:
# total_size   = 110955
# payload_size = 110891
# wrapper      = 64

wrapper = bytearray(64)

fields = {
    0x00: MAGIC,
    0x04: WRAPPER_SIZE + len(dtb),
    0x08: 0x20,
    0x0c: 0x20,
    0x10: 0x01,
    0x14: 0x20,
    0x18: 0x800,
    0x1c: 0,
    0x20: len(dtb),
    0x24: WRAPPER_SIZE,
}

for off, value in fields.items():
    struct.pack_into(">I", wrapper, off, value)

out = bytes(wrapper) + dtb
OUT.write_bytes(out)

print("\n[WRAPPER]")
print(f"SIZE       : {len(wrapper)}")
print(f"TOTAL SIZE : {len(out):,}")
print(f"PAYLOAD    : {len(dtb):,}")
print(f"SHA256     : {sha256(out)}")

# Validate wrapper.
check_magic = struct.unpack_from(">I", out, 0)[0]
check_total = struct.unpack_from(">I", out, 4)[0]
check_payload = struct.unpack_from(">I", out, 0x20)[0]
check_offset = struct.unpack_from(">I", out, 0x24)[0]

print("\n[VALIDATION]")
print(f"magic       : 0x{check_magic:08x}")
print(f"total_size  : {check_total:,}")
print(f"payload     : {check_payload:,}")
print(f"offset      : {check_offset}")

assert check_magic == MAGIC
assert check_total == len(out)
assert check_payload == len(dtb)
assert check_offset == 64
assert struct.unpack_from(">I", out, 64)[0] == 0xD00DFEED

print("\nSTATUS: PASS")
print(f"OUTPUT: {OUT}")
