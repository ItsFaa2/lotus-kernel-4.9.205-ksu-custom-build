
#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import hashlib
import stat

ROOT = Path("/root/kernel-source")
ARCHIVE = ROOT / "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip"
SOURCE = ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"

TARGETS = [
    "arch/arm/boot/dts/include/dt-bindings",
    "arch/arm64/boot/dts/include/dt-bindings",
    "drivers/misc/mediatek/chip/mt6761",
    "arch/arm/boot/dts/sun8i-a23-ippo-q8h-v1.2.dts",
    "arch/arm64/boot/dts/broadcom/bcm2835-rpi.dtsi",
    "include/dt-bindings/input/linux-event-codes.h",
]

print("===== SOURCE DIFFERENCE INVESTIGATION =====")

with ZipFile(ARCHIVE) as z:
    names = set(z.namelist())

    for name in TARGETS:
        path = SOURCE / name
        print(f"\n--- {name} ---")

        matches = [
            item for item in z.infolist()
            if item.filename.rstrip("/") == (
                ARCHIVE.stem + "/" + name
            )
        ]

        print("Archive entry:", "FOUND" if matches else "NOT FOUND")

        if path.is_symlink():
            print("[SYMLINK]", "->", path.readlink())
        elif path.is_file():
            print("[FILE]", path.stat().st_size, "bytes")
            print("[SHA256]", hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir():
            print("[DIRECTORY]")
        else:
            print("[MISSING]")

        if matches:
            info = matches[0]
            mode = info.external_attr >> 16
            print("ZIP size:", info.file_size)
            print("ZIP mode:", oct(stat.S_IFMT(mode)))
            print("ZIP symlink:", stat.S_ISLNK(mode))

            if stat.S_ISLNK(mode):
                print("ZIP link target:", z.read(info).decode(errors="replace"))

print("\n===== INVESTIGATION COMPLETE =====")
