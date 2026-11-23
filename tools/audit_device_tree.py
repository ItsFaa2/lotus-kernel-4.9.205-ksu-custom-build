
#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(
    "/root/kernel-source/work/"
    "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"
)

BASE = ROOT / "arch/arm64/boot/dts"
TARGET = BASE / "mediatek"

print("===== DEVICE TREE INVENTORY =====")

print("\n[DIRECTORY]")
print("Base exists     :", BASE.is_dir())
print("MediaTek exists :", TARGET.is_dir())

if not TARGET.is_dir():
    raise SystemExit("[ERROR] MediaTek DTS directory missing")

files = sorted(
    p for p in TARGET.rglob("*")
    if p.is_file() and p.suffix in (".dts", ".dtsi")
)

print("\nDTS/DTSI files :", len(files))

for path in files:
    relative = path.relative_to(ROOT)
    print(f"[FOUND] {relative} ({path.stat().st_size:,} bytes)")

print("\n===== CERTUS REFERENCES =====")

matches = []
for path in files:
    try:
        content = path.read_text(errors="replace")
    except OSError:
        continue

    if "certus" in content.lower() or "mt6765" in content.lower():
        matches.append(path)

print("Matching files:", len(matches))

for path in matches:
    print("[MATCH]", path.relative_to(ROOT))

print("\n===== AUDIT COMPLETE =====")
