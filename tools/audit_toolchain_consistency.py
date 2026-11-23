
#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess

TOOLS = [
    "gcc", "g++", "make", "clang", "clang-13",
    "ld", "ld.lld-13", "llvm-ar-13",
    "llvm-nm-13", "llvm-objcopy-13",
    "llvm-objdump-13", "llvm-strip-13",
    "python3", "bison", "flex", "dtc",
    "bc", "pahole", "openssl"
]

def run(args):
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=10
        )
        return (result.stdout or result.stderr).strip().splitlines()
    except Exception as exc:
        return [str(exc)]

print("===== TOOLCHAIN CONSISTENCY AUDIT =====")

print("\n[TOOL AVAILABILITY]")
for name in TOOLS:
    path = shutil.which(name)
    print(f"{name:18} : {path or 'NOT FOUND'}")

print("\n[VERSION INFORMATION]")
for name, args in [
    ("gcc", ["gcc", "--version"]),
    ("clang-13", ["clang-13", "--version"]),
    ("ld.lld-13", ["ld.lld-13", "--version"]),
    ("make", ["make", "--version"]),
    ("python3", ["python3", "--version"]),
    ("bison", ["bison", "--version"]),
    ("flex", ["flex", "--version"]),
    ("dtc", ["dtc", "--version"]),
    ("pahole", ["pahole", "--version"]),
    ("openssl", ["openssl", "version"]),
]:
    lines = run(args)
    print(f"\n{name}:")
    print(lines[0] if lines else "NO VERSION OUTPUT")

print("\n[PROJECT ENVIRONMENT]")
for key in [
    "ARCH", "SUBARCH", "CC", "HOSTCC",
    "HOSTLD", "LD", "AR", "NM",
    "OBJCOPY", "OBJDUMP", "STRIP"
]:
    import os
    print(f"{key:12} : {os.environ.get(key, 'NOT SET')}")

print("\n[PROJECT FILES]")
root = Path("/root/kernel-source")
tools = root / "tools"

for name in [
    "project_baseline.txt",
    "runtime_baseline.txt",
]:
    path = tools / name
    print(f"{name:35} : {'FOUND' if path.is_file() else 'MISSING'}")

for name in [
    "boot-lotus.img",
    "lotus-4.9.205_oss-certus-arm64-20240419-15.zip",
]:
    path = root / name
    print(f"{name:65} : {'FOUND' if path.is_file() else 'MISSING'}")

print("\n===== AUDIT COMPLETE =====")
