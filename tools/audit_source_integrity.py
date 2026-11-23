
#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re

SOURCE = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

print("=" * 64)
print("REDMI 6A KERNEL SOURCE INTEGRITY AUDIT")
print("=" * 64)

if not SOURCE.is_dir():
    print("[FATAL] Source directory not found:", SOURCE)
    raise SystemExit(1)

def check(label, path):
    target = SOURCE / path
    status = "FOUND" if target.exists() else "MISSING"
    print(f"[{status}] {label}: {path}")
    return target.exists()

print("\n--- CORE FILES ---")
core = [
    ("Top Makefile", "Makefile"),
    ("Kconfig", "Kconfig"),
    ("Kernel headers", "include/linux"),
    ("Architecture ARM64", "arch/arm64"),
    ("Device Tree", "arch/arm64/boot/dts"),
    ("Scripts", "scripts"),
    ("Security subsystem", "security"),
    ("Driver subsystem", "drivers"),
    ("Filesystem subsystem", "fs"),
    ("Kernel subsystem", "kernel"),
]

results = [check(label, path) for label, path in core]

print("\n--- CONFIGURATION ---")
config = SOURCE / "arch/arm64/configs/certus_defconfig"
check("Certus defconfig", "arch/arm64/configs/certus_defconfig")

if config.is_file():
    data = config.read_text(errors="replace")
    for key in [
        "CONFIG_ARM64",
        "CONFIG_ARCH_MTK_PROJECT",
        "CONFIG_LOCALVERSION",
        "CONFIG_MODULES",
        "CONFIG_KALLSYMS",
        "CONFIG_KPROBES",
        "CONFIG_IKCONFIG",
    ]:
        match = re.search(rf"^{key}=.*$", data, re.M)
        print(f"{key}: {match.group(0) if match else 'NOT DECLARED'}")

print("\n--- KERNEL VERSION ---")
makefile = SOURCE / "Makefile"

if makefile.is_file():
    data = makefile.read_text(errors="replace")
    for key in ["VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION"]:
        match = re.search(rf"^{key}\s*=\s*(.*)$", data, re.M)
        print(f"{key}: {match.group(1).strip() if match else 'NOT DECLARED'}")

print("\n--- CONFIG ARTIFACTS ---")
for path in [
    ".config",
    "include/config/auto.conf",
    "include/generated/autoconf.h",
    "scripts/kconfig/conf",
]:
    check(path, path)

print("\n--- SOURCE FINGERPRINT ---")
digest = hashlib.sha256()

for path in sorted(SOURCE.glob("**/Makefile")):
    try:
        digest.update(str(path.relative_to(SOURCE)).encode())
        digest.update(path.read_bytes())
    except OSError:
        pass

print("Makefile tree SHA256:", digest.hexdigest())
print("Makefile count:", sum(1 for _ in SOURCE.glob("**/Makefile")))

print("\n--- SUMMARY ---")
print(f"Core checks passed: {sum(results)}/{len(results)}")
print("Audit mode: READ ONLY")
print("=" * 64)
