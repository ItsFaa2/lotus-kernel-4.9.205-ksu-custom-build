
#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile, BadZipFile

FILES = [
    Path("/root/kernel-source/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip"),
    Path("/root/kernel-source/lotus-4.9.205_oss-certus-arm64-20240419-15.zip"),
]

print("===== ZIP INTEGRITY AUDIT =====")

for path in FILES:
    print(f"\nFILE: {path.name}")

    if not path.is_file():
        print("[MISSING] File tidak ditemukan")
        continue

    try:
        with ZipFile(path, "r") as archive:
            entries = archive.infolist()
            print(f"Entries : {len(entries)}")
            print(f"Size    : {path.stat().st_size:,} bytes")

            bad_entry = archive.testzip()

            if bad_entry is None:
                print("[OK] CRC seluruh entri valid")
            else:
                print(f"[ERROR] CRC rusak: {bad_entry}")

            print("Sample entries:")
            for entry in entries[:12]:
                print(f"  {entry.filename} ({entry.file_size:,} bytes)")

    except BadZipFile:
        print("[ERROR] Arsip ZIP tidak valid")

print("\n===== AUDIT COMPLETE =====")
