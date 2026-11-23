
#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess

ROOT = Path("/root/kernel-source")

FILES = [
    ROOT / "boot-lotus.img",
    ROOT / "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip",
    ROOT / "lotus-4.9.205_oss-certus-arm64-20240419-15.zip",
    ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/Makefile",
    ROOT / "tools/legacy_audit.json",
]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

print("===== PROJECT INVENTORY AUDIT =====")

for path in FILES:
    print(f"\n[{ 'FOUND' if path.is_file() else 'MISSING' }] {path}")

    if not path.is_file():
        continue

    print(f"Size   : {path.stat().st_size:,} bytes")
    print(f"SHA256 : {sha256(path)}")

    result = subprocess.run(
        ["file", str(path)],
        capture_output=True,
        text=True
    )
    print(f"Format : {result.stdout.strip()}")

print("\n===== AUDIT COMPLETE =====")
