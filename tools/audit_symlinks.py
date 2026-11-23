
#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import stat

ROOT = Path("/root/kernel-source")
ARCHIVE = ROOT / "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15.zip"
SOURCE = ROOT / "work/android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15"

print("===== SYMLINK AUDIT =====")

archive_links = {}
with ZipFile(ARCHIVE) as z:
    prefix = ARCHIVE.stem + "/"

    for info in z.infolist():
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            name = info.filename.removeprefix(prefix)
            target = z.read(info).decode(errors="replace")
            archive_links[name] = target

source_links = {}
for path in SOURCE.rglob("*"):
    if path.is_symlink():
        source_links[path.relative_to(SOURCE).as_posix()] = str(path.readlink())

missing = []
mismatch = []
broken = []

for name, target in archive_links.items():
    path = SOURCE / name

    if name not in source_links:
        missing.append(name)
    elif source_links[name] != target:
        mismatch.append((name, target, source_links[name]))

    if path.is_symlink() and not path.exists():
        broken.append((name, target))

print("Archive symlinks :", len(archive_links))
print("Extracted links  :", len(source_links))
print("Missing links    :", len(missing))
print("Target mismatch  :", len(mismatch))
print("Broken links     :", len(broken))

for name in missing[:20]:
    print("[MISSING]", name)

for name, expected, actual in mismatch[:20]:
    print("[MISMATCH]", name)
    print("  ZIP :", expected)
    print("  DIR :", actual)

for name, target in broken[:20]:
    print("[BROKEN]", name, "->", target)

if not missing and not mismatch and not broken:
    print("\n[OK] Symlink structure matches archive")

print("\n===== AUDIT COMPLETE =====")
