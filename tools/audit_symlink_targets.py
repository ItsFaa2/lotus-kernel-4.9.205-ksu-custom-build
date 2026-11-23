
#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import stat

ROOT = Path("/root/kernel-source")
ARCHIVE = ROOT / "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip"
SOURCE = ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"

def normalize(path):
    return Path(path)

print("===== SYMLINK TARGET AUDIT =====")

checked = 0
missing = 0
broken = 0

with ZipFile(ARCHIVE) as z:
    prefix = ARCHIVE.stem + "/"

    for info in z.infolist():
        mode = info.external_attr >> 16

        if not stat.S_ISLNK(mode):
            continue

        name = info.filename.removeprefix(prefix)
        path = SOURCE / name

        if not path.is_symlink():
            missing += 1
            print("[MISSING]", name)
            continue

        expected = (path.parent / z.read(info).decode()).resolve(strict=False)
        actual = path.resolve(strict=False)

        checked += 1

        if not path.exists():
            broken += 1
            print("[BROKEN]", name)
        elif expected != actual:
            print("[TARGET MISMATCH]", name)
            print("  Expected:", expected)
            print("  Actual  :", actual)

print("\n===== SUMMARY =====")
print("Checked:", checked)
print("Missing:", missing)
print("Broken :", broken)
print("===== AUDIT COMPLETE =====")
