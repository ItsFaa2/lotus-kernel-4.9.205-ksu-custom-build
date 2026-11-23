
#!/usr/bin/env python3
from pathlib import Path
import platform
import subprocess

print("===== RUNNING KERNEL AUDIT =====")

def read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return "Unavailable"

print("\n[PLATFORM]")
print("Kernel release :", platform.release())
print("Architecture   :", platform.machine())
print("Kernel version :", read("/proc/version"))

print("\n[DEVICE IDENTITY]")
for key in [
    "/sys/firmware/devicetree/base/model",
    "/sys/firmware/devicetree/base/compatible",
    "/proc/device-tree/model",
    "/proc/device-tree/compatible",
]:
    value = read(key)
    print(f"{key}: {value.replace(chr(0), ', ')}")

print("\n[KERNEL CONFIG]")
config = read("/proc/config.gz")
if config == "Unavailable":
    print("Compressed config unavailable at this path.")
else:
    print("A compressed config exists; use the saved config audit.")

print("\n[BUILD INFORMATION]")
for key in [
    "/proc/sys/kernel/osrelease",
    "/proc/sys/kernel/version",
]:
    print(f"{key}: {read(key)}")

print("\n===== AUDIT COMPLETE =====")
