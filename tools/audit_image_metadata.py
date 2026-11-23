
#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess

FILES = [
    Path("/root/kernel-source/boot-lotus.img"),
    Path(
        "/root/kernel-source/work/"
        "android_kernel_xiaomi_mt6765-lotus-4.9.205_oss-certus-arm64-20240419-15/"
        "arch/arm64/boot/Image"
    ),
]

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

print("=" * 65)
print("KERNEL IMAGE METADATA AUDIT")
print("=" * 65)

for path in FILES:
    print(f"\nFILE: {path}")

    if not path.is_file():
        print("[NOT FOUND]")
        continue

    print("[FOUND]")
    print("Size:", path.stat().st_size, "bytes")
    print("SHA256:", sha256(path))

    try:
        result = subprocess.run(
            ["file", str(path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("File type:", result.stdout.strip())
    except Exception as exc:
        print("File inspection unavailable:", exc)

print("\nREAD ONLY: no image modified.")
print("=" * 65)
