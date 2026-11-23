
#!/usr/bin/env python3
from pathlib import Path
import gzip

ROOT = Path("/root/kernel-source")
SOURCE = ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
CONFIG = Path("/root/lotus-running.config")
DEFCONFIG = SOURCE / "arch/arm64/configs/certus_defconfig"

KEYS = [
    "CONFIG_MODULES",
    "CONFIG_MODULE_UNLOAD",
    "CONFIG_MODVERSIONS",
    "CONFIG_KALLSYMS",
    "CONFIG_KALLSYMS_ALL",
    "CONFIG_KPROBES",
    "CONFIG_SECURITY",
    "CONFIG_SECURITY_SELINUX",
    "CONFIG_IKCONFIG",
]

def parse(path):
    result = {}
    if not path.is_file():
        return result
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
        elif line.startswith("# CONFIG_") and line.endswith(" is not set"):
            result[line[2:].split()[0]] = "n"
    return result

print("===== KERNEL CONFIG EVIDENCE =====")

running = parse(CONFIG)
default = parse(DEFCONFIG)

print("\n[RUNNING CONFIG]")
print("File:", CONFIG)
for key in KEYS:
    print(f"{key:30}: {running.get(key, 'UNKNOWN')}")

print("\n[CERTUS DEFCONFIG]")
print("File:", DEFCONFIG)
for key in KEYS:
    print(f"{key:30}: {default.get(key, 'NOT DECLARED')}")

print("\n[EVIDENCE SUMMARY]")
print("Running config available:", bool(running))
print("Defconfig available:", bool(default))
print("Comparison is informational; omitted symbols may use Kconfig defaults.")

print("\n===== AUDIT COMPLETE =====")
