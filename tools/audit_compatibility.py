
#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)
CONFIG = Path("/root/lotus-running.config")

def read(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""

def config_value(config, key):
    match = re.search(
        rf"^{re.escape(key)}=(.*)$|^# {re.escape(key)} is not set$",
        config, re.M
    )
    if not match:
        return "UNKNOWN"
    return match.group(1) or "not set"

def report(title, items):
    print(f"\n===== {title} =====")
    for label, value in items:
        print(f"{label:<30}: {value}")

def main():
    if not ROOT.is_dir():
        print("ERROR: source tidak ditemukan")
        return 1

    config = read(CONFIG)
    makefile = read(ROOT / "Makefile")

    version = []
    for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
        match = re.search(rf"^{key}\s*=\s*(\d+)", makefile, re.M)
        version.append(match.group(1) if match else "?")
    kernel_version = ".".join(version)

    report("KERNEL BASE", [
        ("Kernel version", kernel_version),
        ("Architecture", config_value(config, "CONFIG_ARM64")),
        ("MTK project", config_value(config, "CONFIG_ARCH_MTK_PROJECT")),
    ])

    report("LOADABLE MODULE SUPPORT", [
        ("CONFIG_MODULES", config_value(config, "CONFIG_MODULES")),
        ("CONFIG_MODULE_UNLOAD", config_value(config, "CONFIG_MODULE_UNLOAD")),
        ("CONFIG_MODVERSIONS", config_value(config, "CONFIG_MODVERSIONS")),
        ("CONFIG_MODULE_SIG", config_value(config, "CONFIG_MODULE_SIG")),
    ])

    report("KERNEL SYMBOL / DEBUG FEATURES", [
        ("CONFIG_KALLSYMS", config_value(config, "CONFIG_KALLSYMS")),
        ("CONFIG_KALLSYMS_ALL", config_value(config, "CONFIG_KALLSYMS_ALL")),
        ("CONFIG_KPROBES", config_value(config, "CONFIG_KPROBES")),
        ("CONFIG_IKCONFIG", config_value(config, "CONFIG_IKCONFIG")),
    ])

    report("GKI INDICATORS", [
        ("Kernel version >= 5.10", str(
            tuple(map(int, version)) >= (5, 10, 0)
        )),
        ("CONFIG_ANDROID_VENDOR_HOOKS",
         config_value(config, "CONFIG_ANDROID_VENDOR_HOOKS")),
        ("CONFIG_MODULES", config_value(config, "CONFIG_MODULES")),
    ])

    print("\n===== INTERPRETATION =====")
    if kernel_version.startswith("4.9."):
        print("- Source ini merupakan kernel legacy 4.9.")
        print("- Jangan menganggapnya sebagai GKI.")
    print("- CONFIG_MODULES=y menunjukkan dukungan modul kernel.")
    print("- Dukungan modul tidak membuktikan kompatibilitas setiap modul.")
    print("- GKI perlu dinilai dari basis kernel, ABI, vendor modules,")
    print("  dan dokumentasi platform; bukan dari satu opsi Kconfig.")
    print("\nAudit selesai. Tidak ada file yang diubah.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
