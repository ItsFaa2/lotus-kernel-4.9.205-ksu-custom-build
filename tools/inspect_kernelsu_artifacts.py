
#!/usr/bin/env python3
from pathlib import Path
import hashlib
import zipfile
import subprocess
import shutil

FILES = [
    Path("/root/android12-5.10_kernelsu.ko"),
    Path("/root/AnyKernel3-android12-5.10.209_2024-05.zip"),
]

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def inspect_ko(path):
    print("\n[ ELF / MODULE METADATA ]")
    readelf = shutil.which("readelf")

    if not readelf:
        print("readelf tidak tersedia")
        return

    for args in (
        ["-h", str(path)],
        ["-p", ".modinfo", str(path)],
    ):
        result = subprocess.run(
            [readelf, *args],
            capture_output=True,
            text=True
        )
        print(result.stdout or result.stderr or "(no output)")

def inspect_zip(path):
    print("\n[ ZIP CONTENTS ]")
    try:
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                print(f"{item.file_size:>12}  {item.filename}")
    except zipfile.BadZipFile:
        print("ZIP tidak valid atau rusak")

def main():
    for path in FILES:
        print("\n" + "=" * 60)
        print("FILE:", path)

        if not path.is_file():
            print("STATUS: FILE NOT FOUND")
            continue

        print("SIZE:", path.stat().st_size)
        print("SHA256:", sha256(path))

        if path.suffix == ".ko":
            inspect_ko(path)
        elif path.suffix == ".zip":
            inspect_zip(path)

    print("\nInspeksi selesai. Tidak ada file yang diekstrak atau dipasang.")

if __name__ == "__main__":
    main()
