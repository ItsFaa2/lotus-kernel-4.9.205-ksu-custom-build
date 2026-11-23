
#!/usr/bin/env python3
from pathlib import Path
import re
import shutil

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

def section(title):
    print(f"\n===== {title} =====")

def main():
    if not ROOT.is_dir():
        print("[ERROR] Source tidak ditemukan")
        return 1

    makefile = (ROOT / "Makefile").read_text(errors="replace")

    section("LLVM REFERENCES")
    patterns = [
        r"LLVM",
        r"CLANG_TRIPLE",
        r"CLANG_FLAGS",
        r"LLVM_AR",
        r"LLVM_DIS",
        r"LLVM=1",
    ]

    for pattern in patterns:
        matches = [
            f"{i}: {line.strip()}"
            for i, line in enumerate(makefile.splitlines(), 1)
            if re.search(pattern, line, re.I)
        ]
        print(f"\n{pattern}:")
        print("\n".join(matches[:12]) if matches else "NOT FOUND")

    section("COMPILER VARIABLES")
    variables = [
        "CC", "HOSTCC", "LD", "HOSTLD",
        "AR", "NM", "STRIP", "OBJCOPY"
    ]

    for variable in variables:
        matches = re.findall(
            rf"^{variable}\s*[:?+]?=\s*(.*)$",
            makefile,
            re.M
        )
        print(f"{variable:<12}: {matches[:3] or 'NOT FOUND'}")

    section("HOST TOOLS")
    tools = [
        "make", "gcc", "g++", "bc", "bison",
        "flex", "perl", "python3", "openssl",
        "pahole", "dtc"
    ]

    for tool in tools:
        print(f"{tool:<12}: {shutil.which(tool) or 'NOT FOUND'}")

    section("KCONFIG BUILD FILES")
    for name in [
        "scripts/kconfig/Makefile",
        "scripts/kconfig/conf.c",
        "scripts/Makefile.build",
        "scripts/Makefile.host",
        "include/config/auto.conf",
        ".config"
    ]:
        path = ROOT / name
        print(f"{name:<32}: {'PRESENT' if path.exists() else 'ABSENT'}")

    section("SUMMARY")
    print("Static inspection completed.")
    print("No build, patch, or configuration changes performed.")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
