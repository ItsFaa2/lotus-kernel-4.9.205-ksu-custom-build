
#!/usr/bin/env python3
from pathlib import Path
import re
import json

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)
CONFIG = Path("/root/lotus-running.config")

CHECKS = {
    "CONFIG_ARM64": "Architecture ARM64",
    "CONFIG_MODULES": "Kernel module support",
    "CONFIG_MODULE_UNLOAD": "Module unload support",
    "CONFIG_MODVERSIONS": "Module versioning",
    "CONFIG_MODULE_SIG": "Module signature support",
    "CONFIG_KALLSYMS": "Kernel symbol table",
    "CONFIG_KALLSYMS_ALL": "All kernel symbols",
    "CONFIG_KPROBES": "Kprobes support",
    "CONFIG_IKCONFIG": "Embedded kernel config",
    "CONFIG_SECURITY": "Security framework",
    "CONFIG_SECURITY_SELINUX": "SELinux",
    "CONFIG_DEBUG_INFO": "Debug information",
}

def read(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""

def get_config(config, key):
    pattern = (
        rf"^{re.escape(key)}=(.*)$|"
        rf"^# {re.escape(key)} is not set$"
    )
    match = re.search(pattern, config, re.M)

    if not match:
        return "UNKNOWN"

    return match.group(1) if match.group(1) else "not set"

def main():
    if not ROOT.is_dir():
        print("[ERROR] Source directory tidak ditemukan")
        return 1

    config = read(CONFIG)
    makefile = read(ROOT / "Makefile")

    version = []
    for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
        match = re.search(rf"^{key}\s*=\s*(\d+)", makefile, re.M)
        version.append(int(match.group(1)) if match else 0)

    print("=" * 54)
    print(" LEGACY KERNEL COMPATIBILITY AUDIT")
    print("=" * 54)

    print("\n[ KERNEL IDENTITY ]")
    print("Version       :", ".".join(map(str, version)))
    print("Architecture  :", get_config(config, "CONFIG_ARM64"))
    print("MTK Project   :", get_config(config, "CONFIG_ARCH_MTK_PROJECT"))

    print("\n[ CONFIGURATION ]")
    results = {}

    for key, description in CHECKS.items():
        value = get_config(config, key)
        results[key] = value
        print(f"{description:<30}: {value}")

    print("\n[ SOURCE STRUCTURE ]")
    paths = [
        "kernel",
        "security",
        "fs",
        "include/linux",
        "arch/arm64",
        "drivers",
    ]

    for item in paths:
        exists = (ROOT / item).is_dir()
        print(f"{item:<25}: {'PRESENT' if exists else 'MISSING'}")

    print("\n[ COMPATIBILITY NOTES ]")

    if version < [5, 10, 0]:
        print("- Kernel termasuk generasi legacy sebelum GKI 5.10.")

    if results["CONFIG_MODULES"] == "y":
        print("- Dukungan modul kernel aktif.")
    else:
        print("- Dukungan modul tidak terkonfirmasi.")

    if results["CONFIG_MODVERSIONS"] == "y":
        print("- Module versioning aktif; ABI tetap perlu diverifikasi.")

    if results["CONFIG_KPROBES"] == "y":
        print("- Kprobes tersedia pada konfigurasi aktif.")

    print("- Hasil ini bukan bukti kompatibilitas KernelSU.")
    print("- Tidak ada patch, build, atau perubahan konfigurasi.")

    output = {
        "kernel_version": ".".join(map(str, version)),
        "config": results,
        "source": str(ROOT),
        "audit_type": "read_only",
    }

    report = Path.home() / "kernel-source/tools/legacy_audit.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(output, indent=2) + "\n")

    print("\n[ REPORT ]")
    print(report)
    print("\nAudit selesai.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
