#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess

ROOT = Path.home() / "kernel-source" / "FolkPatch-115404"

print("=" * 80)
print("FAA FOLKPATCH 115404 FORENSIC")
print("=" * 80)

print("\n[1] GIT")
print("-" * 80)
for cmd in [
    ["git", "rev-parse", "HEAD"],
    ["git", "describe", "--tags", "--always"],
    ["git", "log", "-1", "--format=%H%n%P%n%s%n%ad", "--date=iso"],
]:
    try:
        print(subprocess.check_output(
            cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip())
    except Exception as e:
        print("ERROR:", e)

print("\n[2] KERNELPATCH / KPATCH REFERENCES")
print("-" * 80)

patterns = [
    r"KernelPatch",
    r"kernelpatch",
    r"kpatch",
    r"0\.13\.9",
    r"4\.9",
    r"aarch64_insn_patch_text",
    r"alias_pte",
    r"image_size",
    r"setup\.kernel_size",
]

files = []
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    if ".git" in p.parts:
        continue
    if p.stat().st_size > 8 * 1024 * 1024:
        continue
    files.append(p)

hits = {}

for p in files:
    try:
        text = p.read_text(errors="ignore")
    except Exception:
        continue

    found = []
    for pat in patterns:
        if re.search(pat, text, re.I):
            found.append(pat)

    if found:
        hits[p] = found

for p, found in sorted(hits.items()):
    print(f"\nFILE: {p.relative_to(ROOT)}")
    print("MATCH:", ", ".join(found))

print("\n[3] IMPORTANT SOURCE FILES")
print("-" * 80)

wanted = [
    "kptools",
    "kpimg",
    "kernelpatch",
    "setup1.S",
    "setup.S",
    "patch",
    "kallsyms",
    "ksyms",
]

for keyword in wanted:
    print(f"\n### {keyword}")
    result = subprocess.run(
        ["find", ".", "-type", "f", "-iname", f"*{keyword}*"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    print(result.stdout.strip() or "(none)")

print("\n[4] FILE TREE - PATCH/KERNEL COMPONENTS")
print("-" * 80)

for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or ".git" in p.parts:
        continue

    s = str(p).lower()

    if any(x in s for x in [
        "kernelpatch",
        "kptools",
        "kpimg",
        "patch",
        "kallsyms",
        "ksym",
        "boot",
    ]):
        try:
            size = p.stat().st_size
        except Exception:
            size = -1

        print(f"{p.relative_to(ROOT)}\t{size}")

print("\n[5] VERSION FILES")
print("-" * 80)

for name in [
    "version.properties",
    "README.md",
    "README_EN.md",
    "Build-Release.sh",
    "scripts/Build-Release.sh",
]:
    p = ROOT / name
    if p.exists():
        print(f"\n### {name}")
        print(p.read_text(errors="ignore")[:12000])

print("\n" + "=" * 80)
print("FORENSIC COMPLETE")
print("=" * 80)
