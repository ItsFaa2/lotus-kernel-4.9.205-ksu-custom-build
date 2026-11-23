
#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess

IMAGE = Path("/root/kernel-source/boot-lotus.img")

TOOLS = [
    "unpackbootimg",
    "magiskboot",
    "avbtool",
    "file",
]

print("=" * 60)
print("ANDROID BOOT IMAGE TOOL AUDIT")
print("=" * 60)

for name in TOOLS:
    path = shutil.which(name)
    print(f"[{'FOUND' if path else 'MISSING'}] {name}")
    if path:
        print("  Path:", path)

print("\n--- IMAGE HEADER ---")

if not IMAGE.is_file():
    print("[ERROR] Image not found")
    raise SystemExit(1)

with IMAGE.open("rb") as f:
    header = f.read(64)

print("Image:", IMAGE)
print("Magic:", repr(header[:8]))
print("Header bytes:", len(header))

if header[:8] == b"ANDROID!":
    print("[OK] Android boot image magic recognized")
else:
    print("[WARNING] Unexpected image magic")

print("\n--- FILE IDENTIFICATION ---")
if shutil.which("file"):
    result = subprocess.run(
        ["file", str(IMAGE)],
        capture_output=True,
        text=True
    )
    print(result.stdout.strip())

print("\nREAD ONLY - no extraction or modification.")
print("=" * 60)
