#!/usr/bin/env python3

from pathlib import Path
import subprocess
import hashlib
import sys

SRC = Path("/root/kernel-source/work/kernel-4.9.205/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15")
BUILD = Path("/root/kernel-source/build/ksu-32915384-49")

VMLINUX = BUILD / "vmlinux"
DTB = BUILD / "arch/arm64/boot/dts/mediatek/mt6765.dtb"
IMAGE = BUILD / "arch/arm64/boot/Image"

if not VMLINUX.is_file():
    raise SystemExit("FATAL: vmlinux tidak ditemukan")

if not DTB.is_file():
    raise SystemExit("FATAL: mt6765.dtb tidak ditemukan")

print("============================================================")
print("FAA KSU ARM64 IMAGE BUILD V1")
print("============================================================")

print("\n[1] EXISTING ARTIFACTS")
print(f"vmlinux : {VMLINUX}")
print(f"size    : {VMLINUX.stat().st_size:,} bytes")
print(f"dtb     : {DTB}")
print(f"size    : {DTB.stat().st_size:,} bytes")

cmd = [
    "make",
    "LLVM=1",
    "LLVM_IAS=1",
    "CROSS_COMPILE=aarch64-linux-gnu-",
    "CROSS_COMPILE_ARM32=arm-linux-gnueabihf-",
    "CC=clang-13",
    "LD=ld.lld-13",
    "AR=llvm-ar-13",
    "NM=llvm-nm-13",
    "OBJCOPY=llvm-objcopy-13",
    "OBJDUMP=llvm-objdump-13",
    "STRIP=llvm-strip-13",
    "-C", str(SRC),
    f"O={BUILD}",
    "ARCH=arm64",
    "-j2",
    "Image",
]

print("\n[2] BUILD COMMAND")
print(" ".join(cmd))

print("\n[3] BUILD")
rc = subprocess.run(cmd).returncode

if rc != 0:
    raise SystemExit(f"\nFATAL: Image build gagal, exit={rc}")

if not IMAGE.is_file():
    raise SystemExit("\nFATAL: make selesai tetapi Image tidak ditemukan")

size = IMAGE.stat().st_size

if size == 0:
    raise SystemExit("\nFATAL: Image berukuran 0 byte")

sha = hashlib.sha256(IMAGE.read_bytes()).hexdigest()

print("\n============================================================")
print("IMAGE BUILD SUCCESS")
print("============================================================")
print(f"PATH   : {IMAGE}")
print(f"SIZE   : {size:,} bytes")
print(f"SHA256 : {sha}")

print("\n[4] FILE")
subprocess.run(["file", str(IMAGE)], check=False)

print("\n[5] DTB")
print(f"PATH   : {DTB}")
print(f"SIZE   : {DTB.stat().st_size:,} bytes")

print("\nBOOT IMAGE STATUS:")
print("NOT TOUCHED")
print("NO FLASH")
