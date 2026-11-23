#!/usr/bin/env python3

from pathlib import Path
import re
import sys

ROOT = Path.home() / "kernel-source"
TOOLS = ROOT / "tools"
OUT = TOOLS / "ksu_api_forensic_v2.txt"

# API yang memang relevan untuk port KernelSU 4.9.
APIS = [
    # Kprobes
    "register_kprobe",
    "unregister_kprobe",
    "register_kretprobe",
    "unregister_kretprobe",

    # Credentials
    "prepare_kernel_cred",
    "commit_creds",
    "override_creds",
    "revert_creds",
    "prepare_creds",
    "current_cred",

    # Task
    "task_struct",
    "find_task_by_vpid",
    "find_task_by_pid_ns",
    "pid_task",
    "get_task_struct",

    # Exec
    "do_execve",
    "do_execveat_common",
    "__do_execve_file",
    "execve",
    "execveat",

    # VFS
    "filp_open",
    "fput",
    "vfs_read",
    "vfs_write",
    "vfs_stat",
    "vfs_unlink",
    "vfs_rename",
    "mnt_want_write",
    "mnt_drop_write",
    "path_umount",

    # Mount
    "do_mount",
    "ksys_mount",
    "do_umount",

    # SELinux
    "current_sid",
    "selinux_state",
    "security_cred_getsecid",
    "security_current_getsecid",

    # Kernel symbol helpers
    "kallsyms_lookup_name",
    "kallsyms_on_each_symbol",

    # OverlayFS
    "ovl_path_real",
    "ovl_dentry_real",
    "ovl_inode_real",
]

TEXT_EXT = {
    ".c", ".h", ".S", ".s", ".inc", ".Kconfig",
    ".mk", ".lds", ".ld", ".txt"
}


def read_text(path):
    try:
        return path.read_text("utf-8", errors="ignore")
    except Exception:
        return ""


def find_roots():
    kernels = []
    ksus = []

    for p in ROOT.iterdir():
        if not p.is_dir():
            continue

        # Kernel root
        if (
            (p / "Makefile").exists()
            and (p / "Kconfig").exists()
            and (p / "arch").is_dir()
            and (p / "drivers").is_dir()
            and (p / "include").is_dir()
            and (p / "kernel").is_dir()
        ):
            kernels.append(p)

        # KSU modern/reference layout
        if (
            (p / "kernel").is_dir()
            and (p / "kernel" / "Makefile").exists()
        ):
            if (
                (p / "kernel" / "Kconfig").exists()
                or (p / "kernel" / "kernel_compat.c").exists()
            ):
                ksus.append(p)

        # KSU legacy embedded driver layout
        if (
            (p / "drivers" / "kernelsu").is_dir()
        ):
            ksus.append(p)

    # Recursive fallback, but ONLY looking for marker files.
    if not kernels:
        for p in ROOT.rglob("Makefile"):
            parent = p.parent

            if any(
                x in parent.parts
                for x in {".git", "build", "out", "__pycache__"}
            ):
                continue

            if (
                (parent / "Kconfig").exists()
                and (parent / "arch").is_dir()
                and (parent / "drivers").is_dir()
                and (parent / "include").is_dir()
                and (parent / "kernel").is_dir()
            ):
                kernels.append(parent)

    if not ksus:
        for marker in (
            "kernel_compat.c",
            "core_hook.c",
            "ksu.c",
        ):
            for p in ROOT.rglob(marker):
                if any(
                    x in p.parts
                    for x in {".git", "build", "out", "__pycache__"}
                ):
                    continue

                ksus.append(p.parent.parent)

    return list(dict.fromkeys(kernels)), list(dict.fromkeys(ksus))


def targeted_files(root, ksu=False):
    if ksu:
        candidates = [
            root / "kernel",
            root / "drivers" / "kernelsu",
        ]
    else:
        candidates = [
            root / "include",
            root / "kernel",
            root / "security",
            root / "fs",
            root / "mm",
            root / "arch" / "arm64",
            root / "drivers",
        ]

    seen = set()

    for base in candidates:
        if not base.exists():
            continue

        for p in base.rglob("*"):
            if not p.is_file():
                continue

            if p.suffix not in TEXT_EXT:
                continue

            if p in seen:
                continue

            seen.add(p)
            yield p


def search_api(files, api):
    rx = re.compile(r"\b" + re.escape(api) + r"\b")
    hits = []

    for p in files:
        text = read_text(p)

        if not text:
            continue

        for n, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append((p, n, line.strip()))

    return hits


def classify_kernel_hit(line):
    if re.search(
        r"\bEXPORT_SYMBOL(?:_GPL)?\s*\(",
        line
    ):
        return "EXPORT"

    if re.search(
        r"\b(?:static\s+)?[\w\s\*]+\b"
        r"[A-Za-z_][A-Za-z0-9_]*\s*\(",
        line
    ):
        return "DECL/DEF"

    return "REFERENCE"


def main():
    print("=" * 78)
    print("FAA KERNELSU TARGETED API FORENSIC V2")
    print("READ-ONLY / NO BUILD / NO PATCH / NO INSTALL")
    print("=" * 78)

    kernels, ksus = find_roots()

    if not kernels:
        print("[ERROR] Kernel root not found")
        return 1

    if not ksus:
        print("[ERROR] KernelSU root not found")
        return 1

    kernel = kernels[0]
    ksu = ksus[0]

    print(f"KERNEL : {kernel}")
    print(f"KSU    : {ksu}")
    print()

    # Build file lists once.
    print("Collecting targeted KSU files...")
    ksu_files = list(targeted_files(ksu, ksu=True))

    print(f"KSU files: {len(ksu_files)}")

    print("Collecting targeted kernel files...")
    kernel_files = list(targeted_files(kernel, ksu=False))

    print(f"KERNEL files: {len(kernel_files)}")
    print()

    report = []

    def out(s=""):
        report.append(s)

    out("FAA KERNELSU TARGETED API FORENSIC V2")
    out("=" * 78)
    out("READ-ONLY")
    out("NO BUILD")
    out("NO PATCH")
    out("NO INSTALL")
    out("NO DELETE")
    out()

    out("[ROOTS]")
    out(f"KERNEL={kernel}")
    out(f"KSU={ksu}")
    out()

    # KSU API usage first.
    out("[KSU API USAGE]")
    out("-" * 78)

    used = []

    for api in APIS:
        hits = search_api(ksu_files, api)

        if hits:
            used.append(api)
            out()
            out(f"### {api}")

            for p, n, line in hits[:20]:
                try:
                    rel = p.relative_to(ksu)
                except ValueError:
                    rel = p

                out(f"KSU {rel}:{n}: {line}")

            if len(hits) > 20:
                out(f"... {len(hits) - 20} more")

    out()
    out(f"KSU APIs FOUND: {len(used)} / {len(APIS)}")
    out()

    # Kernel mapping.
    out("[KERNEL API MAPPING]")
    out("-" * 78)

    missing = []
    found = []

    for api in used:
        hits = search_api(kernel_files, api)

        out()
        out(f"### {api}")

        if not hits:
            missing.append(api)
            out("STATUS: MISSING")
            continue

        found.append(api)

        exports = []
        declarations = []

        for p, n, line in hits:
            kind = classify_kernel_hit(line)

            if kind == "EXPORT":
                exports.append((p, n, line))
            elif kind == "DECL/DEF":
                declarations.append((p, n, line))

        out(f"STATUS: FOUND")
        out(f"HITS: {len(hits)}")
        out(f"DECL/DEF: {len(declarations)}")
        out(f"EXPORT: {len(exports)}")

        for p, n, line in declarations[:10]:
            out(
                f"  DEF {p.relative_to(kernel)}:{n}: {line}"
            )

        for p, n, line in exports[:10]:
            out(
                f"  EXP {p.relative_to(kernel)}:{n}: {line}"
            )

    # Specific high-risk checks.
    out()
    out("[4.9.205 HIGH-RISK API CHECK]")
    out("-" * 78)

    critical = [
        "register_kprobe",
        "unregister_kprobe",
        "prepare_kernel_cred",
        "commit_creds",
        "override_creds",
        "revert_creds",
        "do_execve",
        "do_execveat_common",
        "path_umount",
        "current_sid",
        "selinux_state",
        "security_cred_getsecid",
        "kallsyms_lookup_name",
    ]

    for api in critical:
        ksu_hits = search_api(ksu_files, api)
        kernel_hits = search_api(kernel_files, api)

        out(
            f"{api}: "
            f"KSU={'YES' if ksu_hits else 'NO'} "
            f"KERNEL={'YES' if kernel_hits else 'NO'}"
        )

    # Config evidence.
    out()
    out("[CONFIG EVIDENCE]")
    out("-" * 78)

    configs = [
        kernel / ".config",
        kernel / "arch" / "arm64" / "configs" / "certus_defconfig",
        ROOT / "lotus-running.config",
    ]

    config_keys = [
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
    ]

    for cfg in configs:
        if not cfg.exists():
            continue

        out()
        out(str(cfg))

        values = {}

        for line in read_text(cfg).splitlines():
            m = re.match(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$", line)

            if m:
                values[m.group(1)] = m.group(2)

        for key in config_keys:
            out(
                f"  {key}="
                f"{values.get(key, 'NOT_DECLARED')}"
            )

    # Conclusion.
    out()
    out("[SUMMARY]")
    out("-" * 78)
    out(f"KSU APIs USED        : {len(used)}")
    out(f"KERNEL APIs FOUND    : {len(found)}")
    out(f"KERNEL APIs MISSING  : {len(missing)}")

    if missing:
        out()
        out("MISSING:")
        for x in missing:
            out(f"  - {x}")

    out()
    out("[STATUS]")
    out("This is NOT a compatibility approval.")
    out("FOUND means only that the identifier exists in source.")
    out("It does NOT prove identical prototype or ABI.")
    out("EXPORT means only that an EXPORT_SYMBOL form was found.")
    out("No source was modified.")
    out("No build was executed.")
    out("No boot image was modified.")

    OUT.write_text("\n".join(report), encoding="utf-8")

    print("=" * 78)
    print("FORENSIC COMPLETE")
    print(f"REPORT: {OUT}")
    print("=" * 78)

    return 0


if __name__ == "__main__":
    sys.exit(main())
