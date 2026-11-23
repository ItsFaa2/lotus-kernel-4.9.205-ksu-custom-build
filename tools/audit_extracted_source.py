
#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import hashlib

ROOT = Path("/root/kernel-source")
ARCHIVE = ROOT / "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip"
SOURCE = ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"

def digest(data):
    return hashlib.sha256(data).hexdigest()

print("===== EXTRACTED SOURCE AUDIT =====")

if not ARCHIVE.is_file() or not SOURCE.is_dir():
    print("[ERROR] Archive atau folder source tidak ditemukan")
    raise SystemExit(1)

checked = 0
missing = 0
mismatch = 0
errors = 0

with ZipFile(ARCHIVE) as archive:
    members = [m for m in archive.infolist() if not m.is_dir()]

    for member in members:
        relative = Path(*Path(member.filename).parts[1:])
        extracted = SOURCE / relative

        if not extracted.is_file():
            missing += 1
            if missing <= 20:
                print(f"[MISSING] {relative}")
            continue

        try:
            with archive.open(member) as f:
                archive_hash = hashlib.sha256(f.read()).hexdigest()

            extracted_hash = hashlib.sha256(extracted.read_bytes()).hexdigest()
            checked += 1

            if archive_hash != extracted_hash:
                mismatch += 1
                if mismatch <= 20:
                    print(f"[MISMATCH] {relative}")

        except Exception as exc:
            errors += 1
            print(f"[ERROR] {relative}: {exc}")

print("\n===== SUMMARY =====")
print(f"Checked  : {checked}")
print(f"Missing  : {missing}")
print(f"Mismatch : {mismatch}")
print(f"Errors   : {errors}")

if missing == 0 and mismatch == 0 and errors == 0:
    print("[OK] Extracted source matches archive")
else:
    print("[WARNING] Differences detected")
