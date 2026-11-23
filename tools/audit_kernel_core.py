
#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

FILES = [
    "Makefile",
    "Kconfig",
    "arch/arm64/Makefile",
    "arch/arm64/configs/certus_defconfig",
    "arch/arm64/boot/Makefile",
    "arch/arm64/boot/dts/Makefile",
    "arch/arm64/boot/dts/mediatek",
    "drivers/Makefile",
    "drivers/Kconfig",
    "kernel/Makefile",
    "security/Makefile",
    "include/linux",
]

print("===== KERNEL CORE AUDIT =====")

found = 0
missing = 0

for item in FILES:
    path = ROOT / item

    if path.is_file():
        found += 1
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"[FOUND] {item}")
        print(f"  Size  : {path.stat().st_size:,} bytes")
        print(f"  SHA256: {digest}")

    elif path.is_dir():
        found += 1
        print(f"[FOUND DIRECTORY] {item}")

    else:
        missing += 1
        print(f"[MISSING] {item}")

print("\n===== SUMMARY =====")
print("Found  :", found)
print("Missing:", missing)
print("===== AUDIT COMPLETE =====")
