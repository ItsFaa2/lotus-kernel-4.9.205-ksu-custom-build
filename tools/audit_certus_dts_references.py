
#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

DTS = ROOT / "arch/arm64/boot/dts/mediatek/certus.dts"

print("===== CERTUS DTS INCLUDE AUDIT =====")

if not DTS.is_file():
    raise SystemExit("[ERROR] certus.dts missing")

content = DTS.read_text(errors="replace")

includes = re.findall(
    r'^\s*#include\s*[<"]([^>"]+)[>"]',
    content,
    re.MULTILINE
)

BASES = [
    DTS.parent,
    DTS.parent.parent,
    ROOT / "include",
    ROOT,
]

found = 0
missing = 0

for include in includes:
    matches = [
        base / include
        for base in BASES
        if (base / include).exists()
    ]

    if matches:
        found += 1
        print(f"[FOUND] {include}")
        for path in matches:
            print("  ->", path.relative_to(ROOT))
    else:
        missing += 1
        print(f"[NOT FOUND] {include}")

print("\n===== SUMMARY =====")
print("Total  :", len(includes))
print("Found  :", found)
print("Missing:", missing)
print("===== AUDIT COMPLETE =====")
