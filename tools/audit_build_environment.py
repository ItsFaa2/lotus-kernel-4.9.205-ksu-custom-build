
#!/usr/bin/env python3
from pathlib import Path
import platform
import shutil
import subprocess
import re

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

TOOLS = [
    "python3", "make", "gcc", "clang-13", "clang-14",
    "ld.lld-13", "llvm-ar-13", "llvm-nm-13",
    "llvm-objcopy-13", "readelf", "file"
]

def heading(title):
    print(f"\n{'=' * 14} {title} {'=' * 14}")

def command_version(name):
    path = shutil.which(name)
    if not path:
        return "NOT FOUND"

    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout or result.stderr
        return output.splitlines()[0] if output else "No version output"
    except Exception as exc:
        return f"ERROR: {exc}"

def main():
    heading("SYSTEM")
    print("Platform :", platform.platform())
    print("Machine  :", platform.machine())
    print("Python   :", platform.python_version())

    heading("STORAGE")
    usage = shutil.disk_usage(ROOT)
    print("Source filesystem:")
    print(f"Total    : {usage.total / 1024**3:.2f} GiB")
    print(f"Used     : {usage.used / 1024**3:.2f} GiB")
    print(f"Free     : {usage.free / 1024**3:.2f} GiB")

    heading("MEMORY")
    meminfo = Path("/proc/meminfo").read_text()
    for key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
        match = re.search(rf"^{key}:\s*(.*)$", meminfo, re.M)
        print(f"{key:<15}: {match.group(1) if match else 'UNKNOWN'}")

    heading("TOOLCHAIN")
    for tool in TOOLS:
        print(f"{tool:<20}: {command_version(tool)}")

    heading("SOURCE TREE")
    print("Source exists:", ROOT.is_dir())

    if ROOT.is_dir():
        for item in (
            "Makefile",
            "Kconfig",
            ".config",
            "arch/arm64/configs/certus_defconfig",
            "include/linux",
            "scripts/kconfig/Makefile",
        ):
            path = ROOT / item
            status = "PRESENT" if path.exists() else "ABSENT"
            print(f"{item:<42}: {status}")

        makefile = (ROOT / "Makefile").read_text(errors="replace")
        for key in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
            match = re.search(rf"^{key}\s*=\s*(.*)$", makefile, re.M)
            print(f"{key:<42}: {match.group(1) if match else 'UNKNOWN'}")

    heading("REFERENCE ARTIFACTS")
    artifacts = [
        Path("/root/kernel-source/boot-lotus.img"),
        Path("/root/android12-5.10_kernelsu.ko"),
        Path("/root/AnyKernel3-android12-5.10.209_2024-05.zip"),
    ]

    for path in artifacts:
        if path.is_file():
            print(f"{path.name:<48}: {path.stat().st_size:,} bytes")
        else:
            print(f"{path.name:<48}: NOT FOUND")

    heading("RESULT")
    print("Read-only environment audit completed.")
    print("No source files or device partitions were modified.")

if __name__ == "__main__":
    main()
