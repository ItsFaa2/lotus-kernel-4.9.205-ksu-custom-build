
#!/usr/bin/env python3
from pathlib import Path
import platform
import re
import shutil
import subprocess

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)
CONFIG = Path("/root/lotus-running.config")

def section(name):
    print(f"\n{'=' * 12} {name} {'=' * 12}")

def read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""

def run_version(command):
    path = shutil.which(command)
    if not path:
        return "NOT FOUND"
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True, text=True, timeout=5
        )
        return (result.stdout or result.stderr).splitlines()[0]
    except Exception as exc:
        return str(exc)

def main():
    section("ENVIRONMENT")
    print("Python:", platform.python_version())
    print("Architecture:", platform.machine())
    print("Source exists:", ROOT.is_dir())

    if not ROOT.is_dir():
        print("ERROR: source directory tidak ditemukan")
        return 1

    section("KERNEL VERSION")
    makefile = read_text(ROOT / "Makefile")
    for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION"):
        match = re.search(rf"^{key}\s*=\s*(.*)$", makefile, re.M)
        print(f"{key}: {match.group(1) if match else 'unknown'}")

    section("DEFCONFIG")
    config_dir = ROOT / "arch/arm64/configs"
    for item in sorted(config_dir.glob("*defconfig")):
        print("-", item.name)

    section("RUNNING CONFIG")
    config = read_text(CONFIG)
    keys = (
        "CONFIG_ARM64",
        "CONFIG_MODULES",
        "CONFIG_MODULE_UNLOAD",
        "CONFIG_IKCONFIG",
        "CONFIG_KALLSYMS",
        "CONFIG_KPROBES",
    )
    for key in keys:
        match = re.search(rf"^{key}=.*$|^# {key} is not set$", config, re.M)
        print(f"{key}: {match.group(0) if match else 'NOT PRESENT'}")

    section("KCONFIG SOURCE")
    for name in ("conf.c", "confdata.c", "Makefile"):
        path = ROOT / "scripts/kconfig" / name
        print(f"{name}: {'present' if path.is_file() else 'missing'}")

    section("TOOLCHAIN")
    for tool in ("clang-13", "clang-14", "ld.lld-13",
                 "llvm-ar-13", "llvm-nm-13", "gcc"):
        print(f"{tool}: {run_version(tool)}")

    section("SOURCE METADATA")
    for name in ("README", "README.md", "localversion"):
        path = ROOT / name
        if path.is_file():
            print(f"{name}: present")

    print("\nAudit selesai. Tidak ada file yang diubah.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
