
#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT = Path("/root/kernel-source")
TOOLS = ROOT / "tools"

FILES = {
    "Project baseline": TOOLS / "project_baseline.txt",
    "Runtime baseline": TOOLS / "runtime_baseline.txt",
    "Readiness report": TOOLS / "prebuild_readiness.txt",
    "Boot image": ROOT / "boot-lotus.img",
    "Source archive": ROOT / (
        "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-"
        "certus-arm64-20240419-15.zip"
    ),
    "Flashable archive": ROOT / (
        "lotus-4.9.205_oss-certus-arm64-20240419-15.zip"
    ),
}

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

print("===== FINAL PROJECT VERIFICATION =====")

passed = 0
failed = 0

for label, path in FILES.items():
    exists = path.is_file()
    print(f"\n[{ 'FOUND' if exists else 'MISSING' }] {label}")
    print("Path:", path)

    if exists:
        print("Size:", path.stat().st_size, "bytes")
        if path.suffix in {".img", ".zip"}:
            print("SHA256:", sha256(path))
        passed += 1
    else:
        failed += 1

print("\n===== SUMMARY =====")
print("Found :", passed)
print("Missing:", failed)
print("Result:", "PASS" if failed == 0 else "INCOMPLETE")
print("\nVerification does not establish build or device compatibility.")
print("===== COMPLETE =====")
