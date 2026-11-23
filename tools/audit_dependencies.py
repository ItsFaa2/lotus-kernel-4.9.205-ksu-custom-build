
#!/usr/bin/env python3
import shutil
import subprocess

TOOLS = [
    "bison",
    "flex",
    "dtc",
    "make",
    "gcc",
    "g++",
    "clang-13",
    "ld.lld-13",
    "llvm-ar-13",
    "perl",
    "python3",
    "bc",
    "openssl",
    "pahole",
]

print("=" * 60)
print("KERNEL HOST DEPENDENCY AUDIT")
print("=" * 60)

for tool in TOOLS:
    path = shutil.which(tool)

    if not path:
        print(f"[MISSING] {tool}")
        continue

    try:
        result = subprocess.run(
            [tool, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = (result.stdout or result.stderr).splitlines()
        version = version[0].strip() if version else "Version unavailable"
    except Exception as exc:
        version = str(exc)

    print(f"[FOUND]   {tool}")
    print(f"          Path: {path}")
    print(f"          Info: {version}")

print("=" * 60)
print("AUDIT COMPLETE - NO SOURCE MODIFICATIONS")
print("=" * 60)
