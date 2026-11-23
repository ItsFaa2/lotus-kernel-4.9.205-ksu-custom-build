#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "kernel-source"
TOOLS = ROOT / "tools"
OUT = TOOLS / "ksu_api_forensic_report.txt"

TEXT_EXT = {
    ".c", ".h", ".S", ".s", ".inc", ".Kconfig", ".mk",
    ".txt", ".config", ".lds", ".ld", ".sh", ".py"
}

KSU_FILENAMES = {
    "Kconfig",
    "Makefile",
    "core_hook.c",
    "core_hook.h",
    "kernel_compat.c",
    "kernel_compat.h",
    "ksu.c",
    "ksu.h",
    "ksud.c",
    "ksud.h",
    "sucompat.c",
    "sucompat.h",
    "embed_ksud.c",
    "export_symbol.txt",
    "apk_sign.c",
    "apk_sign.h",
    "allowlist.c",
    "allowlist.h",
    "throne_tracker.c",
    "throne_tracker.h",
    "manager.h",
}

API_PATTERNS = {
    "KPROBES": [
        r"\bregister_kprobe\b",
        r"\bunregister_kprobe\b",
        r"\bregister_kretprobe\b",
        r"\bunregister_kretprobe\b",
        r"\bkprobe\b",
        r"\bkretprobe\b",
    ],
    "CREDENTIALS": [
        r"\bprepare_kernel_cred\b",
        r"\bcommit_creds\b",
        r"\boverride_creds\b",
        r"\brevert_creds\b",
        r"\bprepare_creds\b",
        r"\bget_task_cred\b",
        r"\bcurrent_cred\b",
    ],
    "TASK": [
        r"\btask_struct\b",
        r"\bcurrent\b",
        r"\bfind_task_by_vpid\b",
        r"\bfind_task_by_pid_ns\b",
        r"\bpid_task\b",
        r"\bget_task_struct\b",
    ],
    "EXEC": [
        r"\bdo_execve\b",
        r"\bdo_execveat_common\b",
        r"\b__do_execve_file\b",
        r"\bexecve\b",
        r"\bexecveat\b",
    ],
    "VFS": [
        r"\bvfs_read\b",
        r"\bvfs_write\b",
        r"\bvfs_stat\b",
        r"\bvfs_unlink\b",
        r"\bvfs_rename\b",
        r"\bfilp_open\b",
        r"\bfput\b",
        r"\bdentry\b",
        r"\bpath\b",
        r"\bpath_umount\b",
        r"\bmnt_want_write\b",
        r"\bmnt_drop_write\b",
    ],
    "MOUNT": [
        r"\bdo_mount\b",
        r"\bksys_mount\b",
        r"\bdo_umount\b",
        r"\bpath_umount\b",
        r"\bnamespace\b",
        r"\bmount\b",
        r"\bumount\b",
    ],
    "SELINUX": [
        r"\bcurrent_sid\b",
        r"\bselinux_state\b",
        r"\bsecurity_.*",
        r"\bavc_.*",
        r"\bselinux_.*",
        r"\bsecurity_current_getsecid\b",
    ],
    "FILESYSTEM": [
        r"\bEXT4_FS\b",
        r"\bext4_unregister_sysfs\b",
        r"\boverlayfs\b",
        r"\boverlay\b",
        r"\bsuper_block\b",
        r"\binode\b",
    ],
    "SYMBOL_EXPORT": [
        r"\bEXPORT_SYMBOL\b",
        r"\bEXPORT_SYMBOL_GPL\b",
    ],
}

DECL_PATTERNS = [
    r"^\s*(?:extern\s+)?[\w\s\*\(\),]+\b{sym}\s*\(",
    r"^\s*(?:static\s+)?[\w\s\*\(\),]+\b{sym}\s*\(",
    r"^\s*(?:struct|enum|union)\s+{sym}\b",
]

def safe_read(path: Path) -> str:
    try:
        return path.read_text("utf-8", errors="ignore")
    except Exception:
        return ""

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while True:
                b = f.read(1024 * 1024)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except Exception:
        return "ERROR"

def all_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            yield p

def text_files(root: Path):
    for p in all_files(root):
        if p.suffix in TEXT_EXT or p.name in KSU_FILENAMES:
            yield p

def locate_ksu_roots():
    candidates = []

    for p in ROOT.rglob("*"):
        if not p.is_dir():
            continue

        # Avoid scanning generated build/output directories as KSU roots.
        if any(x in p.parts for x in {
            ".git", "build", "out", "__pycache__"
        }):
            continue

        score = 0

        if (p / "kernel").is_dir():
            if (p / "kernel" / "Kconfig").exists():
                score += 5
            if (p / "kernel" / "Makefile").exists():
                score += 5
            if (p / "kernel" / "kernel_compat.c").exists():
                score += 5

        if (p / "drivers" / "kernelsu").is_dir():
            if (p / "drivers" / "kernelsu" / "Kconfig").exists():
                score += 10
            if (p / "drivers" / "kernelsu" / "Makefile").exists():
                score += 10

        if score:
            candidates.append((score, p))

    return sorted(candidates, reverse=True)

def locate_kernel_roots():
    candidates = []

    for p in ROOT.rglob("Makefile"):
        parent = p.parent

        if any(x in parent.parts for x in {
            ".git", "build", "out", "__pycache__"
        }):
            continue

        if (
            (parent / "Kconfig").exists()
            and (parent / "arch").is_dir()
            and (parent / "include").is_dir()
            and (parent / "kernel").is_dir()
            and (parent / "drivers").is_dir()
        ):
            candidates.append(parent)

    return sorted(set(candidates))

def extract_symbols_from_ksu(ksu_root: Path):
    symbols = defaultdict(set)

    kernel_dir = ksu_root / "kernel"
    drivers_dir = ksu_root / "drivers" / "kernelsu"

    roots = []
    if kernel_dir.exists():
        roots.append(kernel_dir)
    if drivers_dir.exists():
        roots.append(drivers_dir)

    for base in roots:
        for p in text_files(base):
            text = safe_read(p)
            if not text:
                continue

            rel = p.relative_to(ksu_root)

            for category, patterns in API_PATTERNS.items():
                for pattern in patterns:
                    for m in re.finditer(pattern, text, re.MULTILINE):
                        token = m.group(0).strip()
                        if len(token) > 120:
                            token = token[:120]
                        symbols[category].add((token, str(rel)))

    return symbols

def extract_function_names(ksu_root: Path):
    funcs = defaultdict(set)

    for p in text_files(ksu_root / "kernel"):
        text = safe_read(p)
        if not text:
            continue

        rel = p.relative_to(ksu_root)

        # Function calls: foo(...)
        for m in re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            text
        ):
            name = m.group(1)

            if name in {
                "if", "for", "while", "switch", "sizeof",
                "return", "typeof", "likely", "unlikely"
            }:
                continue

            funcs[name].add(str(rel))

    return funcs

def kernel_symbol_index(kernel_root: Path):
    index = defaultdict(list)

    interesting_dirs = [
        kernel_root / "include",
        kernel_root / "kernel",
        kernel_root / "fs",
        kernel_root / "mm",
        kernel_root / "security",
        kernel_root / "arch" / "arm64",
        kernel_root / "drivers",
    ]

    files = []
    for base in interesting_dirs:
        if base.exists():
            files.extend(text_files(base))

    for p in files:
        text = safe_read(p)
        if not text:
            continue

        rel = str(p.relative_to(kernel_root))

        # Definitions/declarations.
        for m in re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(",
            text
        ):
            name = m.group(1)
            index[name].append(rel)

        # Structs / enums / typedefs.
        for m in re.finditer(
            r"\b(?:struct|enum|union)\s+([A-Za-z_][A-Za-z0-9_]*)",
            text
        ):
            index[m.group(1)].append(rel)

    return index

def find_exports(kernel_root: Path):
    exports = defaultdict(list)

    for p in text_files(kernel_root):
        text = safe_read(p)
        if not text:
            continue

        rel = str(p.relative_to(kernel_root))

        for m in re.finditer(
            r"\bEXPORT_SYMBOL(?:_GPL)?\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
            text
        ):
            exports[m.group(1)].append(rel)

    return exports

def extract_config(path: Path):
    result = {}

    if not path.exists():
        return result

    for line in safe_read(path).splitlines():
        m = re.match(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$", line)
        if m:
            result[m.group(1)] = m.group(2)

    return result

def find_configs(kernel_root: Path):
    paths = [
        kernel_root / ".config",
        kernel_root / "arch" / "arm64" / "configs" / "certus_defconfig",
        ROOT / "lotus-running.config",
    ]

    return [p for p in paths if p.exists()]

def scan_config_requirements(ksu_root: Path):
    hits = []

    for p in text_files(ksu_root):
        text = safe_read(p)
        if not text:
            continue

        for line_no, line in enumerate(text.splitlines(), 1):
            if (
                "CONFIG_" in line
                or "depends on" in line
                or "select " in line
            ):
                hits.append(
                    f"{p.relative_to(ksu_root)}:{line_no}: {line.strip()}"
                )

    return hits

def write_report(text):
    TOOLS.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"REPORT: {OUT}")

def main():
    print("=" * 78)
    print("FAA KERNELSU API COMPATIBILITY FORENSIC")
    print("READ-ONLY / NO BUILD / NO PATCH / NO INSTALL")
    print("=" * 78)

    ksu_candidates = locate_ksu_roots()
    kernel_candidates = locate_kernel_roots()

    lines = []

    lines.append("FAA KERNELSU API COMPATIBILITY FORENSIC")
    lines.append("=" * 78)
    lines.append("READ-ONLY")
    lines.append("NO BUILD")
    lines.append("NO PATCH")
    lines.append("NO INSTALL")
    lines.append("NO DELETE")
    lines.append("")

    lines.append("[KSU ROOT CANDIDATES]")
    if not ksu_candidates:
        lines.append("NONE FOUND")
        ksu_root = None
    else:
        for score, p in ksu_candidates[:20]:
            lines.append(f"SCORE={score:02d} {p}")
        ksu_root = ksu_candidates[0][1]

    lines.append("")
    lines.append("[KERNEL ROOT CANDIDATES]")
    if not kernel_candidates:
        lines.append("NONE FOUND")
        kernel_root = None
    else:
        for p in kernel_candidates[:20]:
            lines.append(str(p))
        kernel_root = kernel_candidates[0]

    if not ksu_root or not kernel_root:
        lines.append("")
        lines.append("STATUS: INCOMPLETE")
        lines.append("Required roots could not be located.")
        write_report("\n".join(lines))
        return 1

    lines.append("")
    lines.append(f"[SELECTED KSU ROOT]")
    lines.append(str(ksu_root))

    lines.append("")
    lines.append("[SELECTED KERNEL ROOT]")
    lines.append(str(kernel_root))

    # KSU inventory.
    lines.append("")
    lines.append("[KSU FILE INVENTORY]")

    ksu_files = list(all_files(ksu_root / "kernel"))
    if not ksu_files:
        # Support drivers/kernelsu layout.
        ksu_files = list(all_files(ksu_root / "drivers" / "kernelsu"))

    for p in sorted(ksu_files):
        rel = p.relative_to(ksu_root)
        size = p.stat().st_size
        digest = sha256(p)
        lines.append(f"{rel}\t{size}\t{digest}")

    # Config.
    lines.append("")
    lines.append("[KSU CONFIG REQUIREMENTS]")

    for hit in scan_config_requirements(ksu_root):
        lines.append(hit)

    # API calls.
    symbols = extract_symbols_from_ksu(ksu_root)

    lines.append("")
    lines.append("[KSU API REFERENCE HITS]")

    for category in sorted(symbols):
        lines.append("")
        lines.append(f"--- {category} ---")
        for token, rel in sorted(symbols[category]):
            lines.append(f"{rel}: {token}")

    # Function calls.
    funcs = extract_function_names(ksu_root)

    lines.append("")
    lines.append("[KSU FUNCTION CALL INVENTORY]")

    for name in sorted(funcs):
        if name.startswith(("ksu_", "ksud", "ksu")):
            continue

        refs = sorted(funcs[name])
        if len(refs) > 8:
            refs = refs[:8]

        lines.append(
            f"{name}: " + ", ".join(refs)
        )

    # Kernel symbol index.
    print("Indexing kernel source...")
    kindex = kernel_symbol_index(kernel_root)

    print("Indexing kernel exports...")
    exports = find_exports(kernel_root)

    # Extract unique API names from KSU references.
    candidate_names = set()

    for category_patterns in API_PATTERNS.values():
        for pattern in category_patterns:
            name_pattern = pattern.replace(r"\b", "")
            # Only direct simple names.
            m = re.fullmatch(r"[A-Za-z0-9_.*]+", name_pattern)
            if m and "*" not in name_pattern:
                candidate_names.add(name_pattern)

    # Add function-call names from KSU.
    candidate_names.update(funcs.keys())

    # Compatibility matrix.
    lines.append("")
    lines.append("[KERNEL API COMPATIBILITY MATRIX]")

    for name in sorted(candidate_names):
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            continue

        locations = sorted(set(kindex.get(name, [])))
        export_locations = sorted(set(exports.get(name, [])))

        if locations:
            status = "FOUND"
        else:
            status = "MISSING"

        if export_locations:
            export_status = "EXPORTED"
        else:
            export_status = "NOT_EXPORTED_OR_UNKNOWN"

        lines.append(
            f"{name}\t{status}\t{export_status}\t"
            f"DECLS={len(locations)}\t"
            f"EXPORTS={len(export_locations)}"
        )

        if locations:
            for loc in locations[:5]:
                lines.append(f"  DECL: {loc}")

        if export_locations:
            for loc in export_locations[:5]:
                lines.append(f"  EXP : {loc}")

    # Specific legacy risks.
    lines.append("")
    lines.append("[LEGACY 4.9 RISK CHECKS]")

    risk_patterns = {
        "path_umount": r"\bpath_umount\b",
        "current_sid": r"\bcurrent_sid\b",
        "selinux_state": r"\bselinux_state\b",
        "do_execveat_common": r"\bdo_execveat_common\b",
        "ksys_mount": r"\bksys_mount\b",
        "register_kprobe": r"\bregister_kprobe\b",
        "unregister_kprobe": r"\bunregister_kprobe\b",
        "override_creds": r"\boverride_creds\b",
        "revert_creds": r"\brevert_creds\b",
        "commit_creds": r"\bcommit_creds\b",
        "prepare_kernel_cred": r"\bprepare_kernel_cred\b",
    }

    for name, pattern in risk_patterns.items():
        ksu_hits = []
        kernel_hits = []

        rx = re.compile(pattern)

        for p in text_files(ksu_root):
            text = safe_read(p)
            if rx.search(text):
                ksu_hits.append(str(p.relative_to(ksu_root)))

        for p in text_files(kernel_root):
            text = safe_read(p)
            if rx.search(text):
                kernel_hits.append(str(p.relative_to(kernel_root)))

        lines.append(
            f"{name}: "
            f"KSU={'YES' if ksu_hits else 'NO'} "
            f"KERNEL={'YES' if kernel_hits else 'NO'}"
        )

        for p in ksu_hits[:5]:
            lines.append(f"  KSU: {p}")

        for p in kernel_hits[:5]:
            lines.append(f"  KERNEL: {p}")

    # Config compare.
    lines.append("")
    lines.append("[CONFIGURATION FILES]")

    for p in find_configs(kernel_root):
        lines.append(f"FOUND: {p}")

        cfg = extract_config(p)

        for key in [
            "CONFIG_KPROBES",
            "CONFIG_HAVE_KPROBES",
            "CONFIG_KPROBE_EVENTS",
            "CONFIG_MODULES",
            "CONFIG_MODULE_UNLOAD",
            "CONFIG_MODVERSIONS",
            "CONFIG_KALLSYMS",
            "CONFIG_KALLSYMS_ALL",
            "CONFIG_SECURITY",
            "CONFIG_SECURITY_SELINUX",
            "CONFIG_OVERLAY_FS",
            "CONFIG_EXT4_FS",
            "CONFIG_COMPAT",
            "CONFIG_COMPAT_VDSO",
        ]:
            lines.append(
                f"  {key}={cfg.get(key, 'NOT_DECLARED')}"
            )

    # Hash only important KSU files.
    lines.append("")
    lines.append("[IMPORTANT KSU FILE HASHES]")

    for p in sorted(all_files(ksu_root)):
        if p.name in KSU_FILENAMES:
            lines.append(
                f"{p.relative_to(ksu_root)} "
                f"SHA256={sha256(p)} "
                f"SIZE={p.stat().st_size}"
            )

    # Final status.
    lines.append("")
    lines.append("[FINAL STATUS]")
    lines.append("SOURCE MODIFIED: NO")
    lines.append("BUILD RUN: NO")
    lines.append("PATCH APPLIED: NO")
    lines.append("DEPENDENCY INSTALL: NO")
    lines.append("BOOT IMAGE MODIFIED: NO")
    lines.append("")

    # Conservative conclusion.
    lines.append("[CONCLUSION]")
    lines.append(
        "This report is a source/API compatibility map only."
    )
    lines.append(
        "A FOUND symbol does not prove ABI compatibility."
    )
    lines.append(
        "An EXPORTED symbol does not prove runtime compatibility."
    )
    lines.append(
        "MISSING symbols require manual review before any patch."
    )
    lines.append(
        "No source modification or build was performed."
    )

    write_report("\n".join(lines))

    print("")
    print("=" * 78)
    print("FORENSIC COMPLETE")
    print(f"REPORT: {OUT}")
    print("=" * 78)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nINTERRUPTED")
        sys.exit(130)
    except Exception:
        traceback_text = __import__("traceback").format_exc()
        print(traceback_text)
        sys.exit(1)
