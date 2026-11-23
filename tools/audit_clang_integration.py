
#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

def show_file(path, limit=100):
    print(f"\n--- {path.relative_to(ROOT)} ---")

    if not path.is_file():
        print("FILE NOT FOUND")
        return

    lines = path.read_text(errors="replace").splitlines()

    for number, line in enumerate(lines[:limit], 1):
        print(f"{number:4}: {line}")

def main():
    if not ROOT.is_dir():
        print("[ERROR] Source directory not found")
        return 1

    print("=" * 60)
    print("CLANG INTEGRATION STATIC AUDIT")
    print("=" * 60)

    show_file(ROOT / "scripts/clang-android.sh", 120)

    print("\n--- TOP LEVEL MAKEFILE: CLANG REFERENCES ---")

    makefile = (ROOT / "Makefile").read_text(errors="replace")

    patterns = [
        "CLANG_TRIPLE",
        "CLANG_FLAGS",
        "clang-android.sh",
        "GCC_TOOLCHAIN",
        "LLVM_AR",
        "LLVM_DIS",
        "LLVM=1",
    ]

    lines = makefile.splitlines()

    for pattern in patterns:
        print(f"\n[{pattern}]")
        found = False

        for number, line in enumerate(lines, 1):
            if re.search(re.escape(pattern), line, re.I):
                print(f"{number}: {line.strip()}")
                found = True

        if not found:
            print("NOT FOUND")

    print("\nAudit selesai. Source tidak diubah.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
