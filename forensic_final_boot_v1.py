#!/usr/bin/env python3

from pathlib import Path
import struct
import hashlib

BOOT = Path("/root/kernel-source/boot-lotus-ksu.img")

print("=" * 72)
print("FAA FINAL KSU BOOT FORENSIC V1")
print("=" * 72)

data = BOOT.read_bytes()

def u32(off):
    return struct.unpack_from("<I", data, off)[0]

def u64(off):
    return struct.unpack_from("<Q", data, off)[0]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def page_up(x, page):
    return ((x + page - 1) // page) * page

print(f"FILE   : {BOOT}")
print(f"SIZE   : {len(data):,}")
print(f"SHA256 : {sha(data)}")

# Android boot header v2
magic = data[0:8]
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

name = data[48:64].split(b"\0", 1)[0]
cmdline = data[64:576].split(b"\0", 1)[0].decode(
    "ascii", errors="replace"
)

id_words = struct.unpack_from("<8I", data, 576)

recovery_dtbo_size = u32(608)
recovery_dtbo_offset = u64(616)
header_size = u32(624)
dtb_size = u32(628)
dtb_addr = u64(632)

print()
print("[HEADER]")
print(f"magic              : {magic!r}")
print(f"kernel_size        : {kernel_size:,}")
print(f"kernel_addr        : 0x{kernel_addr:08x}")
print(f"ramdisk_size       : {ramdisk_size:,}")
print(f"ramdisk_addr       : 0x{ramdisk_addr:08x}")
print(f"second_size        : {second_size:,}")
print(f"second_addr        : 0x{second_addr:08x}")
print(f"tags_addr          : 0x{tags_addr:08x}")
print(f"page_size          : {page_size}")
print(f"header_version     : {header_version}")
print(f"os_version        : 0x{os_version:08x}")
print(f"board              : {name!r}")
print(f"cmdline            : {cmdline}")
print(f"recovery_dtbo_size : {recovery_dtbo_size:,}")
print(f"recovery_dtbo_off  : 0x{recovery_dtbo_offset:x}")
print(f"header_size        : {header_size}")
print(f"dtb_size           : {dtb_size:,}")
print(f"dtb_addr           : 0x{dtb_addr:016x}")

print()
print("[EXPECTED HEADER VALUES]")
expected = {
    "kernel_size": 33_943_572,
    "kernel_addr": 0x40080000,
    "ramdisk_size": 789_137,
    "ramdisk_addr": 0x51B00000,
    "second_size": 0,
    "second_addr": 0x40F00000,
    "tags_addr": 0x47880000,
    "page_size": 2048,
    "header_version": 2,
    "recovery_dtbo_size": 0,
    "header_size": 1660,
    "dtb_size": 108_101,
    "dtb_addr": 0x47880000,
}

actual = {
    "kernel_size": kernel_size,
    "kernel_addr": kernel_addr,
    "ramdisk_size": ramdisk_size,
    "ramdisk_addr": ramdisk_addr,
    "second_size": second_size,
    "second_addr": second_addr,
    "tags_addr": tags_addr,
    "page_size": page_size,
    "header_version": header_version,
    "recovery_dtbo_size": recovery_dtbo_size,
    "header_size": header_size,
    "dtb_size": dtb_size,
    "dtb_addr": dtb_addr,
}

all_ok = True

for key, want in expected.items():
    got = actual[key]
    ok = got == want
    print(f"{key:20}: {'PASS' if ok else 'FAIL'} | got={got} expected={want}")
    all_ok &= ok

print()
print("[PAYLOAD OFFSETS]")

header_pages = page_up(header_size, page_size)

kernel_off = header_pages
ramdisk_off = kernel_off + page_up(kernel_size, page_size)
second_off = ramdisk_off + page_up(ramdisk_size, page_size)
dtb_off = second_off + page_up(second_size, page_size)

print(f"header   : 0x{header_pages:x}")
print(f"kernel   : 0x{kernel_off:x}")
print(f"ramdisk  : 0x{ramdisk_off:x}")
print(f"second   : 0x{second_off:x}")
print(f"dtb      : 0x{dtb_off:x}")

print()
print("[PAYLOAD VALIDATION]")

kernel = data[kernel_off:kernel_off + kernel_size]
ramdisk = data[ramdisk_off:ramdisk_off + ramdisk_size]
second = data[second_off:second_off + second_size]
dtb = data[dtb_off:dtb_off + dtb_size]

print(f"kernel actual : {len(kernel):,}")
print(f"kernel sha    : {sha(kernel)}")

print(f"ramdisk actual: {len(ramdisk):,}")
print(f"ramdisk sha   : {sha(ramdisk)}")

print(f"second actual : {len(second):,}")

print(f"dtb actual    : {len(dtb):,}")
print(f"dtb sha       : {sha(dtb)}")

# Kernel ARM64 Image magic:
# Image header magic is "ARM\x64" at offset 0x38.
print()
print("[KERNEL]")
if len(kernel) >= 0x40:
    kmagic = kernel[0x38:0x3c]
    print(f"Image magic @0x38: {kmagic!r}")
    kernel_ok = kmagic == b"ARM\x64"
else:
    kernel_ok = False

print(f"kernel magic     : {'PASS' if kernel_ok else 'FAIL'}")

# MTK DTB wrapper
print()
print("[MTK DTB WRAPPER]")

if len(dtb) >= 64:
    wrapper_magic = struct.unpack_from(">I", dtb, 0)[0]
    wrapper_total = struct.unpack_from(">I", dtb, 4)[0]
    wrapper_payload = struct.unpack_from(">I", dtb, 0x20)[0]
    wrapper_offset = struct.unpack_from(">I", dtb, 0x24)[0]

    print(f"magic       : 0x{wrapper_magic:08x}")
    print(f"total_size  : {wrapper_total:,}")
    print(f"payload     : {wrapper_payload:,}")
    print(f"offset      : {wrapper_offset}")

    fdt_off = wrapper_offset

    if len(dtb) >= fdt_off + 8:
        fdt_magic = struct.unpack_from(">I", dtb, fdt_off)[0]
        fdt_size = struct.unpack_from(">I", dtb, fdt_off + 4)[0]

        print(f"FDT magic   : 0x{fdt_magic:08x}")
        print(f"FDT size    : {fdt_size:,}")
        print(f"FDT SHA256  : {sha(dtb[fdt_off:fdt_off + fdt_size])}")

        wrapper_ok = (
            wrapper_magic == 0xD7B7AB1E
            and wrapper_total == len(dtb)
            and wrapper_payload == len(dtb) - 64
            and wrapper_offset == 64
            and fdt_magic == 0xD00DFEED
            and fdt_size == len(dtb) - 64
        )
    else:
        wrapper_ok = False
else:
    wrapper_ok = False

print(f"wrapper validation: {'PASS' if wrapper_ok else 'FAIL'}")

# Boundary checks
print()
print("[BOUNDARY CHECK]")

end_dtb = dtb_off + dtb_size
print(f"DTB end : 0x{end_dtb:x}")
print(f"FILE end: 0x{len(data):x}")

boundary_ok = end_dtb <= len(data)
print(f"DTB inside image: {'PASS' if boundary_ok else 'FAIL'}")

print()
print("=" * 72)

final_ok = all_ok and kernel_ok and wrapper_ok and boundary_ok

if final_ok:
    print("FINAL FORENSIC STATUS: PASS")
    print("SAFE TO PROCEED TO NEXT VALIDATION STAGE")
else:
    print("FINAL FORENSIC STATUS: FAIL")
    print("DO NOT FLASH")

print("=" * 72)
