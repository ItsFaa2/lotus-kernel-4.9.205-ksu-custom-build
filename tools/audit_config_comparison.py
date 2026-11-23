
#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

FILES = {
    "DEFCONFIG": ROOT / "arch/arm64/configs/certus_defconfig",
    "RUNNING": Path("/root/lotus-running.config"),
}

KEYS = [
    "CONFIG_ARM64",
    "CONFIG_ARCH_MEDIATEK",
    "CONFIG_ARCH_MTK_PROJECT",
    "CONFIG_MODULES",
    "CONFIG_MODULE_UNLOAD",
    "CONFIG_MODVERSIONS",
    "CONFIG_KALLSYMS",
    "CONFIG_KALLSYMS_ALL",
    "CONFIG_KPROBES",
    "CONFIG_SECURITY",
    "CONFIG_SECURITY_SELINUX",
    "CONFIG_IKCONFIG",
    "CONFIG_LOCALVERSION",
    "CONFIG_BUILD_ARM64_DTB_OVERLAY_IMAGE_NAMES",
]

def parse(path):
    result = {}
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value
    return result

print("===== CONFIG COMPARISON AUDIT =====")

configs = {}

for name, path in FILES.items():
    print(f"\n[{name}] {path}")
    if not path.is_file():
        print("[MISSING]")
        continue

    configs[name] = parse(path)
    print("Entries:", len(configs[name]))

if len(configs) == 2:
    print("\n===== SELECTED CONFIGURATION =====")
    for key in KEYS:
        a = configs["DEFCONFIG"].get(key, "(not declared)")
        b = configs["RUNNING"].get(key, "(not declared)")
        print(f"\n{key}")
        print("  Defconfig:", a)
        print("  Running  :", b)

print("\n===== AUDIT COMPLETE =====")
