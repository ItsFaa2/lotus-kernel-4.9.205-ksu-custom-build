#!/usr/bin/env python3

from pathlib import Path
import subprocess
import hashlib

ROOT = Path("/root/kernel-source")
BUILD = ROOT / "build/ksu-32915384-49"

BOOT_ORIG = ROOT / "boot-lotus.img"
KERNEL = BUILD / "arch/arm64/boot/Image"
RAMDISK = BUILD / "original-ramdisk.bin"
DTB = BUILD / "mtk-dtb-wrapper.bin"
OUTPUT = ROOT / "boot-lotus-ksu.img"

CMDLINE = "opt=64S3,32N2,64N2 androidboot.selinux=permissive buildvariant=user"

args = [
    "mkbootimg",

    "--kernel", str(KERNEL),
    "--ramdisk", str(RAMDISK),
    "--dtb", str(DTB),

    "--cmdline", CMDLINE,

    "--base", "0x40000000",
    "--kernel_offset", "0x00080000",
    "--ramdisk_offset", "0x11b00000",
    "--second_offset", "0x00f00000",
    "--tags_offset", "0x07880000",
    "--dtb_offset", "0x07880000",

    "--pagesize", "2048",
    "--header_version", "2",

    "-o", str(OUTPUT),
]

print("=" * 72)
print("FAA KSU BOOT REPACK V1")
print("=" * 72)

for name, path in [
    ("ORIGINAL BOOT", BOOT_ORIG),
    ("KERNEL", KERNEL),
    ("RAMDISK", RAMDISK),
    ("DTB WRAPPER", DTB),
]:
    if not path.is_file():
        raise SystemExit(f"FATAL: missing {name}: {path}")
    print(f"{name:15}: {path}")
    print(f"{'SIZE':15}: {path.stat().st_size:,}")

print()
print("COMMAND:")
print(" ".join(args))
print()

subprocess.run(args, check=True)

data = OUTPUT.read_bytes()

print()
print("=" * 72)
print("REPACK RESULT")
print("=" * 72)
print(f"OUTPUT : {OUTPUT}")
print(f"SIZE   : {len(data):,}")
print(f"SHA256 : {hashlib.sha256(data).hexdigest()}")

print()
print("STATUS: PASS")
