
#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

DEFCONFIG = ROOT / "arch/arm64/configs/certus_defconfig"
RUNNING = Path("/root/lotus-running.config")

KEYS = [
    "CONFIG_ARM64",
    "CONFIG_ARCH_MTK_PROJECT",
    "CONFIG_LOCALVERSION",
    "CONFIG_MODULES",
    "CONFIG_MODULE_UNLOAD",
    "CONFIG_MODVERSIONS",
    "CONFIG_KALLSYMS",
    "CONFIG_KALLSYMS_ALL",
    "CONFIG_KPROBES",
    "CONFIG_IKCONFIG",
    "CONFIG_SECURITY",
    "CONFIG_SECURITY_SELINUX",
    "CONFIG_DEBUG_INFO",
]

def read_config(path):
    result = {}
    if not path.is_file():
        return result

    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()

        if line.startswith("# ") and line.endswith(" is not set"):
            key = line[2:].split(" is not set")[0]
            result[key] = "n"
        elif "=" in line and line.startswith("CONFIG_"):
            key, value = line.split("=", 1)
            result[key] = value

    return result

print("=" * 65)
print("KERNEL CONFIG CONSISTENCY AUDIT")
print("=" * 65)

configs = {
    "certus_defconfig": read_config(DEFCONFIG),
    "running_config": read_config(RUNNING),
}

for name, values in configs.items():
    print(f"\n{name}: {len(values)} declared entries")

print("\n--- CONFIG COMPARISON ---")
print(f"{'CONFIG':32} {'DEFCONFIG':16} {'RUNNING':16}")
print("-" * 65)

for key in KEYS:
    left = configs["certus_defconfig"].get(key, "NOT DECLARED")
    right = configs["running_config"].get(key, "NOT DECLARED")
    print(f"{key:32} {left:16} {right:16}")

print("\n--- VERSION METADATA ---")
makefile = ROOT / "Makefile"

if makefile.is_file():
    data = makefile.read_text(errors="replace")
    for key in ["VERSION", "PATCHLEVEL", "SUBLEVEL"]:
        match = re.search(
            rf"^{key}\s*=\s*(.*)$", data, re.M
        )
        print(f"{key}: {match.group(1).strip() if match else 'UNKNOWN'}")

print("\nREAD ONLY: no files modified.")
print("=" * 65)
