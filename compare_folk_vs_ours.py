#!/usr/bin/env python3

from pathlib import Path
import hashlib
import struct

FOLK = Path.home() / "kernel-source/kernel-forensic/folk-kernel.raw"
OURS = Path.home() / "kernel-source/build/ksu-32915384-49/arch/arm64/boot/Image"

a = FOLK.read_bytes()
b = OURS.read_bytes()

print("=" * 78)
print("FAA KERNEL BINARY COMPARISON")
print("=" * 78)

print(f"FOLK : {len(a):,} bytes")
print(f"OURS : {len(b):,} bytes")
print(f"SIZE : {'MATCH' if len(a) == len(b) else 'DIFF'}")

print()
print("SHA256")
print("FOLK :", hashlib.sha256(a).hexdigest())
print("OURS :", hashlib.sha256(b).hexdigest())

# ARM64 Image header
print()
print("ARM64 IMAGE HEADER")
print("-" * 78)

fields = [
    ("code0", 0x00, "<I"),
    ("code1", 0x04, "<I"),
    ("text_offset", 0x08, "<Q"),
    ("image_size", 0x10, "<Q"),
    ("flags", 0x18, "<Q"),
    ("res2", 0x20, "<Q"),
    ("res3", 0x28, "<Q"),
    ("res4", 0x30, "<Q"),
    ("magic", 0x38, "8s"),
]

for name, off, fmt in fields:
    va = struct.unpack_from(fmt, a, off)[0]
    vb = struct.unpack_from(fmt, b, off)[0]

    if isinstance(va, bytes):
        sa = va
        sb = vb
    else:
        sa = hex(va)
        sb = hex(vb)

    mark = "MATCH" if va == vb else "DIFF"
    print(f"{name:12} FOLK={sa!s:20} OURS={sb!s:20} {mark}")

# Find diff ranges
print()
print("DIFF STATISTICS")
print("-" * 78)

diff_positions = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]

if not diff_positions:
    print("IDENTICAL")
    raise SystemExit(0)

print(f"Different bytes : {len(diff_positions):,}")
print(f"First diff      : 0x{diff_positions[0]:x}")
print(f"Last diff       : 0x{diff_positions[-1]:x}")
print(f"Diff ratio      : {len(diff_positions) / len(a) * 100:.4f}%")

# contiguous ranges
ranges = []
start = prev = diff_positions[0]

for p in diff_positions[1:]:
    if p == prev + 1:
        prev = p
    else:
        ranges.append((start, prev))
        start = prev = p

ranges.append((start, prev))

print(f"Diff ranges     : {len(ranges):,}")

print()
print("FIRST 30 DIFF RANGES")
print("-" * 78)

for s, e in ranges[:30]:
    print(
        f"0x{s:08x}-0x{e:08x} "
        f"({e-s+1:,} bytes)"
    )

# Byte-level windows around first differences
print()
print("FIRST DIFF WINDOWS")
print("-" * 78)

for s, e in ranges[:10]:
    ws = max(0, s - 16)
    we = min(len(a), e + 17)

    print()
    print(f"RANGE 0x{s:x}-0x{e:x}")
    print(f"offset      : 0x{ws:x}-0x{we-1:x}")
    print("FOLK        :", a[ws:we].hex(" "))
    print("OURS        :", b[ws:we].hex(" "))

# Strings around first differences
print()
print("ASCII WINDOWS")
print("-" * 78)

for s, e in ranges[:10]:
    ws = max(0, s - 32)
    we = min(len(a), e + 33)

    def ascii_view(x):
        return "".join(chr(c) if 32 <= c < 127 else "." for c in x)

    print()
    print(f"RANGE 0x{s:x}-0x{e:x}")
    print("FOLK :", ascii_view(a[ws:we]))
    print("OURS :", ascii_view(b[ws:we]))

# Kernel release strings
print()
print("KERNEL RELEASE MARKERS")
print("-" * 78)

markers = [
    b"Linux version ",
    b"clang version ",
    b"gcc version ",
    b"KernelSU:",
    b"LotusKernel",
    b"CONFIG_",
]

for marker in markers:
    print(f"\n[{marker.decode(errors='replace')}]")

    for label, data in [("FOLK", a), ("OURS", b)]:
        pos = data.find(marker)
        if pos >= 0:
            end = data.find(b"\x00", pos)
            if end < 0:
                end = min(pos + 256, len(data))
            print(
                f"{label}: offset=0x{pos:x} "
                f"{data[pos:end].decode(errors='replace')}"
            )
        else:
            print(f"{label}: NOT FOUND")

print()
print("=" * 78)
print("VERDICT")
print("=" * 78)

if len(a) != len(b):
    print("SIZE DIFFERENCE")
elif a == b:
    print("IDENTICAL")
else:
    ratio = len(diff_positions) / len(a)
    if ratio < 0.001:
        print("NEAR-IDENTICAL: very small binary delta")
    elif ratio < 0.01:
        print("SMALL DELTA: likely build/config/source variation")
    else:
        print("SUBSTANTIAL DELTA: likely different kernel build/source/config")

